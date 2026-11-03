import { parseVoiceCommand } from "./voice-command.mjs";
import { makeWav } from "./voice-audio.mjs";
import "./tts-output.mjs";

const startButton = document.querySelector("#voice-start");
const stopButton = document.querySelector("#voice-stop");
const status = document.querySelector("#voice-status");
const error = document.querySelector("#voice-error");
const transcript = document.querySelector("#voice-transcript");
const commandText = document.querySelector("#voice-command");
let current = null;

async function releaseAudio(session) {
    if (session.releasePromise) return session.releasePromise;
    session.releasePromise = (async () => {
        clearTimeout(session.timer);
        clearTimeout(session.flushTimer);
        let failed = false;
        const attempt = action => { try { action(); } catch { failed = true; } };
        for (const track of session.stream?.getTracks() || []) {
            track.onended = null;
            attempt(() => track.stop());
        }
        if (session.node) {
            session.node.onprocessorerror = null;
            session.node.port.onmessage = null;
            attempt(() => session.node.port.close());
            attempt(() => session.node.disconnect());
        }
        if (session.source) attempt(() => session.source.disconnect());
        if (session.context && session.context.state !== "closed") {
            try { await session.context.close(); } catch { failed = true; }
        }
        if (failed) throw new Error("Ses kaynakları kapatılamadı.");
    })();
    return session.releasePromise;
}

async function finish(session, message, failed = false) {
    if (current !== session) return;
    session.controller.abort();
    clearTimeout(session.timer);
    clearTimeout(session.flushTimer);
    try { await releaseAudio(session); }
    catch { failed = true; message = "Mikrofon kaynakları kapatılamadı; sayfayı yenileyin."; }
    finally {
        if (current === session) {
            current = null;
            stopButton.disabled = true;
            window.calculatorVoice.setBusy(false);
            status.textContent = failed ? "Hata" : message;
            error.textContent = failed ? message : "";
            error.hidden = !failed;
            if (failed) commandText.textContent = "";
        }
    }
}

async function upload(session) {
    if (current !== session || session.uploading) return;
    session.uploading = true;
    stopButton.disabled = true;
    status.textContent = "İşleniyor…";
    try {
        await releaseAudio(session); // Microphone is closed before the Azure request.
        if (current !== session) return;
        const form = new FormData();
        form.append("audio", new Blob([makeWav(session.chunks)], { type: "audio/wav" }), "command.wav");
        session.chunks = [];
        session.timer = setTimeout(() => session.controller.abort(), 65000);
        const response = await fetch("/api/voice-input", { method: "POST", body: form, signal: session.controller.signal });
        const data = await response.json();
        if (current !== session) return;
        if (!response.ok) throw new Error(data.error || "Ses kaydı işlenemedi.");
        if (typeof data.text !== "string") throw new Error("Geçersiz tanıma yanıtı.");
        transcript.textContent = data.text;
        const command = parseVoiceCommand(data.text); // No calculator mutation before full validation.
        commandText.textContent = command.normalized;
        const calculation = await window.calculatorVoice.apply(command);
        if (current !== session) return;
        if (!calculation) {
            await finish(session, "Hesaplama hatası; hesap makinesi hata alanını kontrol edin.", true);
            return;
        }
        commandText.textContent = `${command.normalized} ${calculation.result}`;
        await finish(session, "İşlem tamamlandı.");
    } catch (failure) {
        await finish(session, failure.name === "AbortError" ? "İşlem zaman aşımına uğradı veya iptal edildi." : failure.message, true);
    }
}

function stop() {
    const session = current;
    if (!session || session.uploading || session.stopping) return;
    session.stopping = true;
    stopButton.disabled = true;
    if (!session.node || !session.recording) { void finish(session, "Kayıt iptal edildi."); return; }
    status.textContent = "Kayıt durduruluyor…";
    session.node.port.postMessage("flush");
    session.flushTimer = setTimeout(() => void finish(session, "Son ses parçaları alınamadı; tekrar deneyin.", true), 3000);
}

startButton.addEventListener("click", async () => {
    if (current || startButton.disabled) return;
    const session = { controller: new AbortController(), chunks: [], bytes: 0 };
    current = session;
    window.calculatorVoice.setBusy(true);
    stopButton.disabled = false;
    transcript.textContent = commandText.textContent = error.textContent = "";
    error.hidden = true;
    status.textContent = "Mikrofon izni bekleniyor…";
    try {
        if (!navigator.mediaDevices?.getUserMedia || !window.AudioContext || !window.AudioWorkletNode) {
            throw new Error("Bu tarayıcı mikrofon/AudioWorklet desteklemiyor. Localhost üzerinde güncel tarayıcı kullanın.");
        }
        const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true } });
        if (current !== session) { stream.getTracks().forEach(track => track.stop()); return; }
        session.stream = stream;
        for (const track of stream.getTracks()) track.onended = () => void finish(session, "Mikrofon bağlantısı kesildi.", true);
        session.context = new AudioContext();
        await session.context.audioWorklet.addModule("/static/voice-worklet.mjs");
        if (current !== session) return;
        session.node = new AudioWorkletNode(session.context, "voice-capture", { outputChannelCount: [1] });
        session.node.onprocessorerror = () => void finish(session, "Ses dönüştürme işlemi başarısız.", true);
        session.node.port.onmessage = ({ data }) => {
            if (current !== session) return;
            if (data.type === "pcm") {
                session.bytes += data.buffer.byteLength;
                if (session.bytes > 480000) { void finish(session, "Kayıt 15 saniye sınırını aştı.", true); return; }
                session.chunks.push(data.buffer);
            } else if (data.type === "flushed") void upload(session);
        };
        session.source = session.context.createMediaStreamSource(stream);
        session.source.connect(session.node);
        session.node.connect(session.context.destination); // Worklet outputs only silence.
        await session.context.resume();
        if (current !== session) return;
        session.recording = true;
        session.node.port.postMessage("start");
        status.textContent = "Dinleniyor… İngilizce komutu söyleyin (en fazla 15 saniye).";
        session.timer = setTimeout(stop, 15000);
    } catch (failure) {
        await finish(session, failure.name === "NotAllowedError" ? "Mikrofon izni reddedildi; izin verip tekrar deneyin." : "Mikrofon başlatılamadı. İzinleri ve ses aygıtını kontrol edin.", true);
    }
});
stopButton.addEventListener("click", stop);
window.addEventListener("pagehide", () => { if (current) void finish(current, "Kayıt iptal edildi."); });
