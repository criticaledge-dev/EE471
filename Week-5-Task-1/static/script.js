"use strict";

const form = document.getElementById("tts-form");
const button = document.getElementById("generate");
const status = document.getElementById("status");
const error = document.getElementById("error");
const result = document.getElementById("result");
const audio = document.getElementById("audio");
const download = document.getElementById("download");
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
  if (pending) return;
  clearAudio();
  error.hidden = true;
  error.textContent = "";
  pending = true;
  button.disabled = true;
  form.setAttribute("aria-busy", "true");
  status.textContent = "Ses oluşturuluyor…";
  try {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: document.getElementById("text").value,
        language: document.getElementById("language").value,
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
    button.disabled = false;
    form.removeAttribute("aria-busy");
  }
});

window.addEventListener("pagehide", clearAudio);
