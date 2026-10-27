import { SpeechQueue } from "./tts-queue.mjs";
import { readTtsResponse } from "./tts-response.mjs";
import { TtsAudioCache } from "./tts-cache.mjs";

const toggle = document.querySelector("#tts-enabled");
if (toggle) {
    const error = document.querySelector("#tts-error");
    const status = document.querySelector("#tts-status");
    const metrics = document.querySelector("#tts-metrics");
    let latestMetrics = null;
    function renderMetrics() {
        if (!metrics) return;
        const timing = latestMetrics ? `İstek/önbellek bekleme: ${Math.round(latestMetrics.requestWaitMs)} ms; oynatma sırası bekleme: ${Math.round(latestMetrics.playbackQueueMs)} ms. ` : "Henüz süre ölçülmedi. ";
        metrics.textContent = timing + `HTTP: ${cache.stats.requests}; önbellek: ${cache.stats.hits}; paylaşılan istek: ${cache.stats.shared}.`;
    }
    const cache = new TtsAudioCache(async (text, signal) => {
            const response = await fetch("/api/tts", { method: "POST", signal,
                headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
            return readTtsResponse(response);
    }, { onChange: renderMetrics });
    const queue = new SpeechQueue({
        fetchAudio: (text, signal) => cache.get(text, signal),
        onCancel: () => cache.cancel(),
        onMetrics(value) { latestMetrics = value; renderMetrics(); },
        createAudio: url => new Audio(url),
        createURL: blob => URL.createObjectURL(blob),
        revokeURL: url => URL.revokeObjectURL(url),
        onError(message) { error.textContent = message; error.hidden = !message; },
        onStatus(message) { if (status) status.textContent = message; },
    });
    window.calculatorAudio = queue;
    renderMetrics();
    // Browsers may restore a checked checkbox without firing a change event.
    queue.setEnabled(toggle.checked);
    toggle.addEventListener("change", () => queue.setEnabled(toggle.checked));
    window.addEventListener("pagehide", () => { toggle.checked = false; queue.setEnabled(false); });
}
