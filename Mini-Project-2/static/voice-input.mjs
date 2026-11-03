import { makeWav } from "./voice-audio.mjs";

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

export class LibraryMicrophone {
    constructor({ acquire, release, runCommandText, onState, onTranscript, onControls, onFailure = () => {}, environment = browserVoiceEnvironment() }) {
        Object.assign(this, { acquire, release, runCommandText, onState, onTranscript, onControls, onFailure });
        this.env = environment;
        this.current = null;
        this.libraryBusy = false;
        this.env.onPageHide(() => { void this.cancel(); });
        this.controls();
    }
    controls() {
        const s = this.current;
        this.onControls({ startDisabled: Boolean(s) || this.libraryBusy,
            stopDisabled: !s || s.phase !== "recording", cancelDisabled: !s || s.phase === "executing" });
    }
    setLibraryBusy(value) { this.libraryBusy = value; this.controls(); }
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
            if (failed) throw new Error("Audio cleanup failed. Refresh the page before recording again.");
        })();
        return s.releasePromise;
    }
    async finish(s, message, error = false) {
        if (this.current !== s || s.finishing) return;
        s.finishing = true; s.controller.abort(); this.clearTimers(s);
        try { await this.releaseAudio(s); }
        catch { error = true; message += " Audio cleanup failed; refresh the page."; }
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
        return this.finish(s, s.phase === "executing"
            ? "Canceled locally. A command may already have reached the server; check the collection. Cancellation does not undo a mutation."
            : "Recording canceled. No command was executed.");
    }
    async start() {
        if (this.current || this.libraryBusy) return;
        const token = this.acquire();
        if (!token) return;
        const s = { token, controller: new AbortController(), chunks: [], bytes: 0, phase: "permission" };
        this.current = s; this.onTranscript("");
        this.state(s, "permission", "Waiting for microphone permission…");
        s.permissionTimer = this.env.setTimer(() => void this.finish(s, "Microphone permission timed out. No command was executed.", true), 45000);
        try {
            const stream = await this.env.getMedia();
            if (this.current !== s || s.finishing) { stream.getTracks().forEach(track => track.stop()); return; }
            s.stream = stream;
            for (const track of stream.getTracks()) track.onended = () => void this.finish(s, "Microphone disconnected. No command was executed.", true);
            s.context = this.env.createContext();
            await s.context.audioWorklet.addModule("/static/voice-worklet.mjs");
            if (this.current !== s || s.finishing) return;
            s.node = this.env.createNode(s.context);
            s.node.onprocessorerror = () => void this.finish(s, "Microphone PCM processing failed. No command was executed.", true);
            s.node.port.onmessage = ({ data }) => {
                if (this.current !== s || s.finishing || s.uploading) return;
                if (data.type === "pcm") {
                    if (!(data.buffer instanceof ArrayBuffer) || !data.buffer.byteLength || data.buffer.byteLength % 2) {
                        void this.finish(s, "Invalid PCM chunk. No command was executed.", true); return;
                    }
                    s.bytes += data.buffer.byteLength;
                    if (s.bytes > 960000) { void this.finish(s, "Recording exceeds 30 seconds. No command was executed.", true); return; }
                    s.chunks.push(data.buffer);
                } else if (data.type === "flushed") void this.upload(s);
            };
            s.source = s.context.createMediaStreamSource(stream);
            s.source.connect(s.node); s.node.connect(s.context.destination); // Worklet outputs silence.
            await s.context.resume();
            if (this.current !== s || s.finishing) return;
            this.env.clearTimer(s.permissionTimer); s.permissionTimer = undefined;
            this.state(s, "recording", "Recording en-US… Stop to process (maximum 30 seconds).");
            s.node.port.postMessage("start");
            s.recordTimer = this.env.setTimer(() => this.stop(), 30000);
        } catch (error) {
            await this.finish(s, error.name === "NotAllowedError"
                ? "Microphone permission was denied. Allow access and try again."
                : "Microphone could not start. Check browser support, permission and device settings.", true);
        }
    }
    stop() {
        const s = this.current;
        if (!s || s.phase !== "recording" || s.finishing) return;
        this.state(s, "flushing", "Stopping; waiting for the final PCM chunk…");
        s.flushTimer = this.env.setTimer(() => void this.finish(s, "Final PCM chunk was not received. Incomplete audio was not sent.", true), 3000);
        s.node.port.postMessage("flush");
    }
    async upload(s) {
        if (this.current !== s || s.uploading || s.finishing) return;
        s.uploading = true;
        try {
            this.state(s, "uploading", "Converting PCM to WAV and sending recording…");
            await this.releaseAudio(s);
            if (this.current !== s || s.finishing) return;
            const form = new FormData();
            form.append("audio", new Blob([makeWav(s.chunks)], { type: "audio/wav" }), "command.wav");
            form.append("language", "en-US"); s.chunks = [];
            s.requestTimer = this.env.setTimer(() => {
                s.timedOut = true;
                void this.finish(s, "Speech recognition timed out. No command was executed.", true);
            }, 90000);
            const pending = this.env.fetch("/api/voice-input", { method: "POST", body: form, signal: s.controller.signal });
            this.state(s, "recognizing", "Recording submitted; waiting for complete Azure recognition…");
            const response = await pending;
            const data = await response.json();
            if (this.current !== s || s.finishing || s.controller.signal.aborted) return;
            if (!response.ok) {
                const message = response.status === 422 ? "No complete speech was recognized. No command was executed."
                    : response.status === 503 ? "Speech recognition is not configured on the server."
                    : "Speech recognition could not be completed. No command was executed.";
                await this.finish(s, "Speech recognition: " + message, true); return;
            }
            if (data.language !== "en-US" || typeof data.text !== "string" || !data.text.trim()) {
                await this.finish(s, "Speech recognition returned no complete transcript. No command was executed.", true); return;
            }
            this.env.clearTimer(s.requestTimer); s.requestTimer = undefined;
            this.onTranscript(data.text); // Preserve original text/case/punctuation; no separate parser.
            this.state(s, "executing", "Recognition complete; running the command through the Library API…");
            s.executing = true;
            const result = await this.runCommandText(data.text, { voiceToken: s.token, signal: s.controller.signal });
            if (this.current !== s || s.finishing) return;
            if (result?.ok) await this.finish(s, result.warning ? "Command succeeded; see the separate list refresh warning." : "Voice command completed. See the command result.");
            else await this.finish(s, result?.stage === "parser"
                ? "Speech was recognized, but the command could not be parsed. Edit the Command text and use Run command; that is a manual correction."
                : "The Library command failed. See the Command error; no automatic retry was made.");
        } catch (error) {
            if (this.current !== s || s.finishing) return;
            await this.finish(s, s.executing ? "The command outcome could not be confirmed. Check the collection; no automatic retry was made."
                : s.timedOut ? "Speech recognition timed out. No command was executed."
                : "The recording could not be sent or recognized. No command was executed.", true);
        }
    }
}

export function mountVoiceInput({ document, acquire, release, runCommandText, onFailure, environment }) {
    const start = document.getElementById("voice-start");
    if (!start) return null;
    const stop = document.getElementById("voice-stop"), cancel = document.getElementById("voice-cancel");
    const status = document.getElementById("voice-status"), error = document.getElementById("voice-error");
    const transcript = document.getElementById("voice-transcript"), input = document.getElementById("command-text");
    const microphone = new LibraryMicrophone({ acquire, release, runCommandText, onFailure, environment,
        onState(message, failed) { status.textContent = message; error.textContent = failed ? message : ""; error.hidden = !failed; },
        onTranscript(text) { transcript.textContent = text; if (text) input.value = text; },
        onControls(state) { start.disabled = state.startDisabled; stop.disabled = state.stopDisabled; cancel.disabled = state.cancelDisabled; },
    });
    start.addEventListener("click", () => microphone.start());
    stop.addEventListener("click", () => microphone.stop());
    cancel.addEventListener("click", () => microphone.cancel());
    return microphone;
}
