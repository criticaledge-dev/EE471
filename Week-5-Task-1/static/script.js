"use strict";

const form = document.getElementById("stt-form");
const button = document.getElementById("transcribe");
const statusArea = document.getElementById("status");
const errorArea = document.getElementById("error");
const result = document.getElementById("result");
const transcript = document.getElementById("transcript");
const download = document.getElementById("download");
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
  if (pending) return;
  clearResult();
  errorArea.hidden = true;
  errorArea.textContent = "";
  pending = true;
  button.disabled = true;
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
    button.disabled = false;
    form.removeAttribute("aria-busy");
  }
});

document.getElementById("copy").addEventListener("click", async () => {
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
