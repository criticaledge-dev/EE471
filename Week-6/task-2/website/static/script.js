"use strict";
const form = document.getElementById("classify-form");
const input = document.getElementById("image");
const button = document.getElementById("classify");
const preview = document.getElementById("preview");
const status = document.getElementById("status");
const error = document.getElementById("error");
const result = document.getElementById("result");
let previewUrl = null;
let controller = null;
let generation = 0;
let busy = false;

function clearResult() {
  result.hidden = true;
  document.getElementById("top-class").textContent = "";
  document.getElementById("scores").replaceChildren();
  error.textContent = "";
  error.hidden = true;
}

function clearPreview() {
  preview.hidden = true;
  preview.removeAttribute("src");
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
}

input.addEventListener("change", () => {
  generation += 1;
  controller?.abort();
  busy = false;
  input.disabled = false;
  clearResult();
  clearPreview();
  const file = input.files[0];
  button.disabled = !file;
  status.textContent = file ? "Ready to classify." : "Choose an image to begin.";
  if (file) {
    previewUrl = URL.createObjectURL(file);
    preview.src = previewUrl;
    preview.hidden = false;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy || !input.files[0]) return;
  const ticket = ++generation;
  clearResult();
  busy = true;
  button.disabled = true;
  input.disabled = true;
  status.textContent = "Classifying…";
  controller = new AbortController();
  const activeController = controller;
  const timeout = window.setTimeout(() => activeController.abort(), 70000);
  const body = new FormData();
  body.append("image", input.files[0]);
  try {
    const response = await fetch("/api/classify", { method: "POST", body, signal: activeController.signal });
    const data = await response.json().catch(() => { throw new Error("Server returned an invalid response."); });
    if (ticket !== generation) return;
    if (!response.ok) throw new Error(data.error || "Classification failed.");
    if (data.status !== "succeeded" || !data.output) throw new Error("Prediction did not complete.");
    const scores = Object.entries(data.output).sort((a, b) => b[1] - a[1]);
    document.getElementById("top-class").textContent = `Top class: ${scores[0][0]} (${(scores[0][1] * 100).toFixed(2)}%)`;
    for (const [label, score] of scores) {
      const row = document.createElement("li");
      row.textContent = `${label}: ${(score * 100).toFixed(2)}%`;
      document.getElementById("scores").append(row);
    }
    result.hidden = false;
    status.textContent = "Classification complete.";
  } catch (failure) {
    if (ticket !== generation) return;
    error.textContent = failure.name === "AbortError" ? "Request timed out. Please try again." : failure.message;
    error.hidden = false;
    status.textContent = "Classification failed.";
  } finally {
    window.clearTimeout(timeout);
    if (ticket === generation) {
      busy = false;
      controller = null;
      input.disabled = false;
      button.disabled = !input.files[0];
    }
  }
});

window.addEventListener("pagehide", () => {
  generation += 1;
  controller?.abort();
  clearPreview();
});
