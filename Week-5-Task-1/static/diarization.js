"use strict";

(() => {
  const start = document.getElementById("diarization-start");
  const stop = document.getElementById("diarization-stop");
  const language = document.getElementById("diarization-language");
  const status = document.getElementById("diarization-status");
  const error = document.getElementById("diarization-error");
  const interim = document.getElementById("diarization-interim");
  const finals = document.getElementById("diarization-finals");
  let current = null;

  function label(speaker) {
    return !speaker || speaker === "Unknown" ? "Unknown — konuşmacı belirlenemedi" : `Konuşmacı ${speaker}`;
  }

  function speakerClass(speaker) {
    if (!speaker || speaker === "Unknown") return "speaker-unknown";
    let hash = 0;
    for (const character of speaker) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
    return `speaker-${hash % 6}`;
  }

  async function releaseAudio(session) {
    if (session.audioRelease) return session.audioRelease;
    session.audioRelease = (async () => {
    clearTimeout(session.timer);
    if (session.media) session.media.getTracks().forEach(track => {
      if (session.onTrackEnded) track.removeEventListener("ended", session.onTrackEnded);
      try { track.stop(); } catch {}
    });
    try { if (session.source) session.source.disconnect(); } catch {}
    if (session.node) {
      try { session.node.disconnect(); } catch {}
      session.node.port.onmessage = null;
      session.node.onprocessorerror = null;
      session.node.port.close();
    }
    if (session.context && session.context.state !== "closed") {
      await session.context.close().catch(() => {});
    }
    })();
    return session.audioRelease;
  }

  async function finish(session, message = null, completed = false) {
    if (current !== session) return;
    current = null;
    session.closed = true;
    clearTimeout(session.deadline);
    await releaseAudio(session);
    if (session.ws) {
      session.ws.onopen = session.ws.onmessage = session.ws.onerror = session.ws.onclose = null;
      try { session.ws.close(); } catch {}
    }
    stop.disabled = true;
    language.disabled = false;
    setSpeechBusy(false);
    interim.textContent = "";
    status.textContent = completed ? "Oturum tamamlandı; son Azure sonuçları alındı." : "Dinleme kapalı; sonuçlar kısmi olabilir.";
    if (message) {
      error.textContent = message;
      error.hidden = false;
    }
  }

  function requestStop(session) {
    if (current !== session || session.closed || session.stopping) return;
    session.stopping = true;
    stop.disabled = true;
    status.textContent = "Durduruluyor; son ses parçaları ve Azure sonuçları bekleniyor…";
    clearTimeout(session.timer);
    if (!session.ready) {
      void finish(session, "Bağlanma kullanıcı tarafından iptal edildi.");
      return;
    }
    session.node.port.postMessage({ type: "flush" });
    clearTimeout(session.deadline);
    session.deadline = setTimeout(() => void finish(session, "Sonuçların tamamlandığı doğrulanamadı; bağlantı zaman aşımı."), 18000);
  }

  function onWorklet(session, data) {
    if (current !== session || session.closed || !session.ready) return;
    if (data.type === "pcm") {
      if (session.ws.readyState !== WebSocket.OPEN || session.ws.bufferedAmount > 65536) {
        void finish(session, "Ses bağlantısı yetişemedi; kayıt tamamlanamadı.");
        return;
      }
      session.ws.send(data.pcm);
    } else if (data.type === "flushed") {
      session.stopping = true;
      stop.disabled = true;
      status.textContent = "Durduruluyor; son Azure sonuçları bekleniyor…";
      session.ws.send(JSON.stringify({ type: "stop" }));
      void releaseAudio(session);
      clearTimeout(session.deadline);
      session.deadline = setTimeout(() => void finish(session, "Sonuçların tamamlandığı doğrulanamadı; bağlantı zaman aşımı."), 15000);
    } else if (data.type === "error") {
      void finish(session, data.error);
    }
  }

  function onServer(session, message) {
    if (current !== session || session.closed) return;
    if (message.type === "ready") {
      if (session.ready || session.stopping || message.sample_rate !== 16000 || message.channels !== 1 || message.bits_per_sample !== 16) {
        void finish(session, "Beklenmeyen canlı ses yapılandırması.");
        return;
      }
      clearTimeout(session.deadline);
      session.ready = true;
      status.textContent = "Dinleniyor — canlı sonuçlar geldikçe gösterilir (en fazla 60 saniye).";
      session.node.port.postMessage({ type: "start" });
      session.source.connect(session.node);
      session.timer = setTimeout(() => requestStop(session), 60000);
    } else if (message.type === "ack") {
      if (session.node && !session.audioRelease) session.node.port.postMessage({ type: "credit" });
    } else if (message.type === "interim") {
      interim.textContent = `${label(message.speaker_id)}: ${message.text}`;
      interim.className = `live-interim ${speakerClass(message.speaker_id)}`;
    } else if (message.type === "final") {
      const key = message.result_id || JSON.stringify([message.offset_ms, message.duration_ms, message.speaker_id, message.text]);
      if (session.seen.has(key)) return;
      if (session.seen.size >= 128) {
        void finish(session, "Canlı sonuç sayısı sınırına ulaşıldı.");
        return;
      }
      session.seen.add(key);
      const row = document.createElement("li");
      row.className = speakerClass(message.speaker_id);
      const heading = document.createElement("strong");
      heading.textContent = label(message.speaker_id);
      row.appendChild(heading);
      if (typeof message.offset_ms === "number") {
        const timing = document.createElement("span");
        timing.textContent = ` · ${(message.offset_ms / 1000).toFixed(2)} s`
          + (typeof message.duration_ms === "number" ? ` / ${(message.duration_ms / 1000).toFixed(2)} s` : "");
        row.appendChild(timing);
      }
      const text = document.createElement("p");
      text.textContent = message.text;
      row.appendChild(text);
      finals.appendChild(row);
      interim.textContent = "";
    } else if (message.type === "stop_requested") {
      requestStop(session);
    } else if (message.type === "stopping") {
      status.textContent = "Durduruluyor; Azure oturum bitişi bekleniyor…";
    } else if (message.type === "completed") {
      void finish(session, null, true);
    } else if (message.type === "error") {
      void finish(session, message.error || "Canlı diarization tamamlanamadı.");
    }
  }

  start.addEventListener("click", async () => {
    if (speechBusy || current) return;
    const session = { seen: new Set(), ready: false, stopping: false, closed: false };
    current = session;
    setSpeechBusy(true);
    stop.disabled = false;
    language.disabled = true;
    error.hidden = true;
    error.textContent = interim.textContent = "";
    finals.replaceChildren();
    status.textContent = "Mikrofon izni bekleniyor; ardından bağlanılacak…";
    try {
      session.media = await navigator.mediaDevices.getUserMedia({ audio: {
        channelCount: 1, echoCancellation: true, noiseSuppression: true,
      } });
      if (current !== session) { session.media.getTracks().forEach(track => track.stop()); return; }
      session.onTrackEnded = () => requestStop(session);
      for (const track of session.media.getTracks()) track.addEventListener("ended", session.onTrackEnded);
      session.context = new AudioContext(); // Use its actual rate; do not relabel samples.
      await session.context.audioWorklet.addModule("/static/pcm-worklet.mjs");
      if (current !== session) { await releaseAudio(session); return; }
      session.node = new AudioWorkletNode(session.context, "live-pcm", { numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [1] });
      session.node.port.onmessage = ({ data }) => onWorklet(session, data);
      session.node.onprocessorerror = () => void finish(session, "Ses işleyicisi hata verdi.");
      session.source = session.context.createMediaStreamSource(session.media);
      // Processor output is always zero: graph active, microphone never monitored.
      session.node.connect(session.context.destination);
      await session.context.resume();
      if (current !== session) { await releaseAudio(session); return; }
      status.textContent = "Bağlanıyor — Azure hazır olana kadar ses gönderilmez…";
      session.ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/diarization`);
      session.deadline = setTimeout(() => void finish(session, "Canlı bağlantı hazır olmadı; zaman aşımı."), 22000);
      session.ws.onopen = () => {
        if (current === session) session.ws.send(JSON.stringify({ type: "start", language: language.value }));
      };
      session.ws.onmessage = ({ data }) => {
        try { onServer(session, JSON.parse(data)); }
        catch { void finish(session, "Geçersiz canlı sunucu yanıtı."); }
      };
      session.ws.onerror = () => void finish(session, "WebSocket bağlantı hatası.");
      session.ws.onclose = () => void finish(session, "Bağlantı tamamlanma onayı olmadan kapandı; sonuçlar kısmi olabilir.");
    } catch (failure) {
      void finish(session, failure.name === "NotAllowedError" ? "Mikrofon izni verilmedi; kayıt başlamadı." : "Mikrofon veya canlı bağlantı başlatılamadı.");
    }
  });

  stop.addEventListener("click", () => { if (current) requestStop(current); });
  window.addEventListener("pagehide", () => { if (current) void finish(current); });
})();
