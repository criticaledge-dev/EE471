"use strict";

let speechBusy = false;
function setSpeechBusy(busy) {
  speechBusy = busy;
  document.getElementById("tts-generate").disabled = busy;
  document.getElementById("stt-transcribe").disabled = busy;
  document.getElementById("translation-submit").disabled = busy;
}

(() => {
  const form = document.getElementById("translation-form");
  const source = document.getElementById("translation-source");
  const target = document.getElementById("translation-target");
  const status = document.getElementById("translation-status");
  const error = document.getElementById("translation-error");
  const result = document.getElementById("translation-result");
  const original = document.getElementById("translation-original");
  const translated = document.getElementById("translation-text");

  function clearResult() {
    result.hidden = true;
    original.textContent = "";
    translated.textContent = "";
  }

  source.addEventListener("change", () => {
    target.value = source.value === "en-US" ? "tr" : "en";
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (speechBusy) return;
    clearResult();
    error.hidden = true;
    error.textContent = "";
    setSpeechBusy(true);
    form.setAttribute("aria-busy", "true");
    status.textContent = "Konuşma çevriliyor…";
    try {
      const response = await fetch("/api/translate", { method: "POST", body: new FormData(form) });
      const body = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(body && typeof body.error === "string" ? body.error : "Konuşma çevrilemedi. Tekrar deneyin.");
      }
      if (!body || typeof body.recognized_text !== "string" || !body.recognized_text.trim()
          || typeof body.translated_text !== "string" || !body.translated_text.trim()) {
        throw new Error("Sunucudan eksiksiz bir çeviri sonucu alınamadı.");
      }
      original.textContent = body.recognized_text;
      translated.textContent = body.translated_text;
      result.hidden = false;
      status.textContent = "Çeviri hazır.";
    } catch (failure) {
      clearResult();
      status.textContent = "";
      error.textContent = failure instanceof TypeError
        ? "Sunucuya ulaşılamadı. Bağlantınızı kontrol edip tekrar deneyin."
        : failure.message;
      error.hidden = false;
    } finally {
      setSpeechBusy(false);
      form.removeAttribute("aria-busy");
    }
  });
})();

(() => {

const form = document.getElementById("tts-form");
const button = document.getElementById("tts-generate");
const status = document.getElementById("tts-status");
const error = document.getElementById("tts-error");
const result = document.getElementById("tts-result");
const audio = document.getElementById("tts-audio");
const download = document.getElementById("tts-download");
let objectUrl = null;
let pending = false;

function clearAudio() {
  result.hidden = true;
  audio.pause();
  audio.removeAttribute("src");
  audio.load();
  download.removeAttribute("href");
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = null;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (pending || speechBusy) return;
  clearAudio();
  error.hidden = true;
  error.textContent = "";
  pending = true;
  setSpeechBusy(true);
  form.setAttribute("aria-busy", "true");
  status.textContent = "Ses oluşturuluyor…";
  try {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: document.getElementById("tts-text").value,
        language: document.getElementById("tts-language").value,
      }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(typeof body.error === "string" ? body.error : "Ses üretilemedi. Tekrar deneyin.");
    }
    if (!(response.headers.get("Content-Type") || "").startsWith("audio/wav")) {
      throw new Error("Sunucudan beklenmeyen bir yanıt alındı.");
    }
    const blob = await response.blob();
    if (!blob.size) throw new Error("Sunucudan boş ses yanıtı alındı.");
    objectUrl = URL.createObjectURL(blob);
    audio.src = objectUrl;
    download.href = objectUrl;
    result.hidden = false;
    status.textContent = "Ses hazır. Oynatabilir veya WAV olarak indirebilirsiniz.";
  } catch (failure) {
    clearAudio();
    status.textContent = "";
    error.textContent = failure instanceof TypeError
      ? "Sunucuya ulaşılamadı. Bağlantınızı kontrol edip tekrar deneyin."
      : failure.message;
    error.hidden = false;
  } finally {
    pending = false;
    setSpeechBusy(false);
    form.removeAttribute("aria-busy");
  }
});

window.addEventListener("pagehide", clearAudio);

})();

(() => {

const form = document.getElementById("stt-form");
const button = document.getElementById("stt-transcribe");
const statusArea = document.getElementById("stt-status");
const errorArea = document.getElementById("stt-error");
const result = document.getElementById("stt-result");
const transcript = document.getElementById("stt-transcript");
const download = document.getElementById("stt-download");
let pending = false;
let objectUrl = null;

function clearResult() {
  result.hidden = true;
  transcript.textContent = "";
  download.removeAttribute("href");
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = null;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (pending || speechBusy) return;
  clearResult();
  errorArea.hidden = true;
  errorArea.textContent = "";
  pending = true;
  setSpeechBusy(true);
  form.setAttribute("aria-busy", "true");
  statusArea.textContent = "Ses tanınıyor…";
  try {
    const response = await fetch("/api/stt", { method: "POST", body: new FormData(form) });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(typeof body.error === "string" ? body.error : "Ses tanınamadı. Tekrar deneyin.");
    }
    if (typeof body.text !== "string" || !body.text.trim()) {
      throw new Error("Sunucudan geçerli bir metin sonucu alınamadı.");
    }
    transcript.textContent = body.text;
    objectUrl = URL.createObjectURL(new Blob([body.text], { type: "text/plain;charset=utf-8" }));
    download.href = objectUrl;
    result.hidden = false;
    statusArea.textContent = "Metin hazır.";
  } catch (failure) {
    clearResult();
    statusArea.textContent = "";
    errorArea.textContent = failure instanceof TypeError
      ? "Sunucuya ulaşılamadı. Bağlantınızı kontrol edip tekrar deneyin."
      : failure.message;
    errorArea.hidden = false;
  } finally {
    pending = false;
    setSpeechBusy(false);
    form.removeAttribute("aria-busy");
  }
});

document.getElementById("stt-copy").addEventListener("click", async () => {
  const currentText = transcript.textContent;
  if (!currentText || pending) return;
  try {
    await navigator.clipboard.writeText(currentText);
    if (transcript.textContent === currentText && !pending) statusArea.textContent = "Metin kopyalandı.";
  } catch {
    if (transcript.textContent === currentText && !pending) {
      errorArea.textContent = "Kopyalama izni alınamadı. Metni seçerek kopyalayabilir veya TXT olarak indirebilirsiniz.";
      errorArea.hidden = false;
    }
  }
});

window.addEventListener("pagehide", clearResult);

})();
