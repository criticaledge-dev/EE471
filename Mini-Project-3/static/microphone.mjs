import { makeWav } from "./voice-audio.mjs";

// Allow for the first local model load on a Windows-mounted WSL environment.
const TRANSCRIPTION_TIMEOUT_MS = 300000;

// The browser boundary is injectable for offline tests. Native timers retain Window this.
export function browserVoiceEnvironment() {
    return {
        getMedia: () => navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true } }),
        createContext: () => new AudioContext(),
        createNode: context => new AudioWorkletNode(context, "voice-capture", { outputChannelCount: [1] }),
        fetch: (...args) => fetch(...args),
        setTimer: (fn, ms) => globalThis.setTimeout(fn, ms),
        clearTimer: id => globalThis.clearTimeout(id),
        onPageHide: fn => globalThis.addEventListener?.("pagehide", fn),
    };
}

export class ChatMicrophone {
    constructor({ acquire, release, onState, onTranscript, onControls, onFailure = () => {}, environment = browserVoiceEnvironment() }) {
        Object.assign(this, { acquire, release, onState, onTranscript, onControls, onFailure });
        this.env = environment;
        this.current = null;
        this.inputBusy = false;
        this.env.onPageHide(() => { void this.cancel(); });
        this.controls();
    }
    controls() {
        const s = this.current;
        this.onControls({ startDisabled: Boolean(s) || this.inputBusy,
            stopDisabled: !s || s.phase !== "recording", cancelDisabled: !s });
    }
    setInputBusy(value) { this.inputBusy = value; this.controls(); }
    state(s, phase, message) {
        if (this.current !== s) return;
        s.phase = phase; this.onState(message, false); this.controls();
    }
    clearTimers(s) {
        for (const key of ["permissionTimer", "recordTimer", "flushTimer", "requestTimer"]) {
            if (s[key] !== undefined) { this.env.clearTimer(s[key]); s[key] = undefined; }
        }
    }
    async releaseAudio(s) {
        if (s.releasePromise) return s.releasePromise;
        s.releasePromise = (async () => {
            this.clearTimers(s);
            let failed = false;
            const attempt = fn => { try { fn(); } catch { failed = true; } };
            for (const track of s.stream?.getTracks() || []) { track.onended = null; attempt(() => track.stop()); }
            if (s.node) {
                s.node.onprocessorerror = null; s.node.port.onmessage = null;
                attempt(() => s.node.port.close()); attempt(() => s.node.disconnect());
            }
            if (s.source) attempt(() => s.source.disconnect());
            if (s.context && s.context.state !== "closed") {
                try { await s.context.close(); } catch { failed = true; }
            }
            if (failed) throw new Error("Mikrofon kapatılamadı. Yeniden kaydetmeden önce sayfayı yenile.");
        })();
        return s.releasePromise;
    }
    async finish(s, message, error = false) {
        if (this.current !== s || s.finishing) return;
        s.finishing = true; s.controller.abort(); this.clearTimers(s);
        try { await this.releaseAudio(s); }
        catch { error = true; message += " Mikrofon kapatılamadı; sayfayı yenile."; }
        finally {
            if (this.current === s) {
                s.chunks = [];
                this.current = null; this.release(s.token);
                this.onState(message, error); this.controls();
                if (error) this.onFailure(message);
            }
        }
    }
    async cancel() {
        const s = this.current;
        if (!s) return;
        return this.finish(s, "Kayıt iptal edildi.");
    }
    async start() {
        if (this.current || this.inputBusy) return;
        const token = this.acquire();
        if (!token) return;
        const s = { token, controller: new AbortController(), chunks: [], bytes: 0, phase: "permission" };
        this.current = s;
        this.state(s, "permission", "Mikrofon izni bekleniyor…");
        s.permissionTimer = this.env.setTimer(() => void this.finish(s, "Mikrofon izni zaman aşımına uğradı.", true), 45000);
        try {
            const stream = await this.env.getMedia();
            if (this.current !== s || s.finishing) { stream.getTracks().forEach(track => track.stop()); return; }
            s.stream = stream;
            for (const track of stream.getTracks()) track.onended = () => void this.finish(s, "Mikrofon bağlantısı kesildi.", true);
            s.context = this.env.createContext();
            await s.context.audioWorklet.addModule("/static/voice-worklet.mjs");
            if (this.current !== s || s.finishing) return;
            s.node = this.env.createNode(s.context);
            s.node.onprocessorerror = () => void this.finish(s, "Mikrofon sesi işlenemedi.", true);
            s.node.port.onmessage = ({ data }) => {
                if (this.current !== s || s.finishing || s.uploading) return;
                if (data.type === "pcm") {
                    if (!(data.buffer instanceof ArrayBuffer) || !data.buffer.byteLength || data.buffer.byteLength % 2) {
                        void this.finish(s, "Geçersiz ses parçası.", true); return;
                    }
                    s.bytes += data.buffer.byteLength;
                    if (s.bytes > 960000) { void this.finish(s, "Kayıt 30 saniye sınırını aşıyor.", true); return; }
                    s.chunks.push(data.buffer);
                } else if (data.type === "flushed") void this.upload(s);
            };
            s.source = s.context.createMediaStreamSource(stream);
            s.source.connect(s.node); s.node.connect(s.context.destination); // Worklet outputs silence.
            await s.context.resume();
            if (this.current !== s || s.finishing) return;
            this.env.clearTimer(s.permissionTimer); s.permissionTimer = undefined;
            this.state(s, "recording", "Dinleniyor… Bitirince mikrofona tekrar bas (en fazla 30 saniye).");
            s.node.port.postMessage("start");
            s.recordTimer = this.env.setTimer(() => this.stop(), 30000);
        } catch (error) {
            await this.finish(s, error.name === "NotAllowedError"
                ? "Mikrofon izni verilmedi. Erişime izin verip tekrar dene."
                : "Mikrofon açılamadı. Tarayıcı iznini ve cihazı kontrol et.", true);
        }
    }
    stop() {
        const s = this.current;
        if (!s || s.phase !== "recording" || s.finishing) return;
        this.state(s, "flushing", "Kayıt tamamlanıyor…");
        s.flushTimer = this.env.setTimer(() => void this.finish(s, "Ses kaydı tamamlanamadı; kayıt gönderilmedi.", true), 3000);
        s.node.port.postMessage("flush");
    }
    async upload(s) {
        if (this.current !== s || s.uploading || s.finishing) return;
        s.uploading = true;
        try {
            this.state(s, "uploading", "Ses kaydı hazırlanıyor…");
            await this.releaseAudio(s);
            if (this.current !== s || s.finishing) return;
            const form = new FormData();
            form.append("audio", new Blob([makeWav(s.chunks)], { type: "audio/wav" }), "speech.wav");
            form.append("language", "en-US"); s.chunks = [];
            s.requestTimer = this.env.setTimer(() => {
                void this.finish(s, "Sesi yazıya çevirme zaman aşımına uğradı.", true);
            }, TRANSCRIPTION_TIMEOUT_MS);
            const pending = this.env.fetch("/api/voice-input", { method: "POST", body: form, signal: s.controller.signal });
            this.state(s, "recognizing", "Konuşma yazıya çevriliyor…");
            const response = await pending;
            const data = await response.json();
            if (this.current !== s || s.finishing || s.controller.signal.aborted) return;
            if (!response.ok) {
                const message = data.error || "Ses yazıya çevrilemedi.";
                await this.finish(s, "Ses tanıma: " + message, true); return;
            }
            if (data.language !== "en-US" || typeof data.text !== "string" || !data.text.trim()) {
                await this.finish(s, "Tam bir transkript alınamadı.", true); return;
            }
            this.env.clearTimer(s.requestTimer); s.requestTimer = undefined;
            this.onTranscript(data.text);
            await this.finish(s, "Metin hazır. Düzenleyip Gönder’e basabilirsin.");
        } catch (error) {
            if (this.current !== s || s.finishing) return;
            await this.finish(s, "Ses gönderilemedi veya yazıya çevrilemedi.", true);
        }
    }
}
