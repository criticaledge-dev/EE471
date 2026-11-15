"use strict";
const form = document.getElementById("classify-form");
const input = document.getElementById("image");
const button = document.getElementById("classify");
const preview = document.getElementById("preview");
const status = document.getElementById("status");
const error = document.getElementById("error");
const models = ["baseline", "optimized"];
let previewUrl = null;
let controller = null;
let generation = 0;
let busy = false;

function clearResult() {
  for (const name of models) {
    document.getElementById(`${name}-result`).hidden = true;
    document.getElementById(`${name}-top-class`).textContent = "";
    document.getElementById(`${name}-scores`).replaceChildren();
    const failure = document.getElementById(`${name}-error`);
    failure.textContent = "";
    failure.hidden = true;
  }
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
  status.textContent = "Comparing both models...";
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
    if (!data.results || !models.every(name => data.results[name])) throw new Error("Invalid comparison response.");
    let successes = 0;
    for (const name of models) {
      const prediction = data.results[name];
      if (prediction.status !== "succeeded" || !prediction.output) {
        const failure = document.getElementById(`${name}-error`);
        failure.textContent = prediction.error || "Prediction did not complete.";
        failure.hidden = false;
        continue;
      }
      const scores = Object.entries(prediction.output.top3).sort((a, b) => b[1] - a[1]);
      const title = name === "baseline" ? "Baseline" : "Optimized";
      document.getElementById(`${name}-top-class`).textContent = `${title} prediction: ${scores[0][0]} (${(scores[0][1] * 100).toFixed(2)}%)`;
      for (const [label, score] of scores) {
        const row = document.createElement("li");
        row.textContent = `${label}: ${(score * 100).toFixed(2)}%`;
        document.getElementById(`${name}-scores`).append(row);
      }
      document.getElementById(`${name}-result`).hidden = false;
      successes += 1;
    }
    status.textContent = successes === 2 ? "Comparison complete." : successes === 1 ? "One model completed; see the other card's error." : "Both models failed; see the cards.";
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
