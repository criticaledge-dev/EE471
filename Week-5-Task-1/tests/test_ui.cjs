"use strict";

// Offline DOM/fetch mocks, not a real browser or Azure verification.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function setup() {
  const ids = ["tts-form", "tts-generate", "tts-status", "tts-error", "tts-result",
    "tts-audio", "tts-download", "tts-text", "tts-language", "stt-form",
    "stt-transcribe", "stt-status", "stt-error", "stt-result", "stt-transcript",
    "stt-download", "stt-copy"];
  const elements = Object.fromEntries(ids.map(id => [id, {
    textContent: "", hidden: false, disabled: false, value: "",
    addEventListener(name, callback) { this[name] = callback; },
    setAttribute(name, value) { this[name] = value; },
    removeAttribute(name) { delete this[name]; },
    pause() {}, load() {},
  }]));
  elements["tts-text"].value = "Hello world";
  elements["tts-language"].value = "en-US";
  const requests = [], revoked = [], copied = [], urls = [];
  const unload = [];
  const context = {
    document: { getElementById: id => {
      assert.ok(elements[id], `Unexpected DOM id: ${id}`);
      return elements[id];
    } },
    window: { addEventListener: (_name, callback) => unload.push(callback) },
    FormData: class { constructor(form) { this.form = form; } },
    Blob, TypeError,
    navigator: { clipboard: { async writeText(text) { copied.push(text); } } },
    URL: {
      createObjectURL(blob) { urls.push(blob); return `blob:result-${urls.length}`; },
      revokeObjectURL: url => revoked.push(url),
    },
    fetch: (url, options) => new Promise((resolve, reject) => requests.push({ url, options, resolve, reject })),
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../static/script.js"), "utf8"), context);
  return {
    elements, requests, revoked, copied, urls, unload,
    submit: kind => elements[`${kind}-form`].submit({ preventDefault() {} }),
  };
}

function wavResponse() {
  return { ok: true, headers: { get: () => "audio/wav" }, blob: async () => new Blob(["mock WAV"]) };
}
function textResponse(text) { return { ok: true, json: async () => ({ text }) }; }
function errorResponse() { return { ok: false, json: async () => ({ error: "Service unavailable" }) }; }

test("TTS and STT prevent concurrent sends and keep independent results", async () => {
  const ui = setup(), e = ui.elements;
  let work = ui.submit("tts");
  assert.equal(e["tts-generate"].disabled, true);
  assert.equal(e["stt-transcribe"].disabled, true);
  await ui.submit("tts");
  await ui.submit("stt");
  assert.equal(ui.requests.length, 1);
  assert.equal(ui.requests[0].url, "/api/tts");
  assert.deepEqual(JSON.parse(ui.requests[0].options.body), { text: "Hello world", language: "en-US" });
  ui.requests[0].resolve(wavResponse());
  await work;
  assert.equal(e["tts-result"].hidden, false);
  const wavUrl = e["tts-audio"].src;
  work = ui.submit("stt");
  await ui.submit("tts");
  assert.equal(ui.requests.length, 2);
  assert.equal(ui.requests[1].url, "/api/stt");
  assert.equal(ui.requests[1].options.body.form, e["stt-form"]);
  assert.equal(e["tts-audio"].src, wavUrl);
  ui.requests[1].resolve(textResponse("<script>literal transcript</script>"));
  await work;
  assert.equal(e["stt-transcript"].textContent, "<script>literal transcript</script>");
  assert.equal(e["stt-result"].hidden, false);
  assert.equal(e["tts-audio"].src, wavUrl);
  assert.equal(e["tts-generate"].disabled, false);
  assert.equal(e["stt-transcribe"].disabled, false);
  await e["stt-copy"].click();
  assert.deepEqual(ui.copied, [e["stt-transcript"].textContent]);
  assert.equal(await ui.urls[1].text(), e["stt-transcript"].textContent);
  ui.unload.forEach(callback => callback());
  assert.deepEqual(ui.revoked, ["blob:result-1", "blob:result-2"]);
});

test("failed requests clear only their own old result and allow retry", async () => {
  for (const kind of ["tts", "stt"]) {
    const ui = setup(), e = ui.elements;
    let work = ui.submit(kind);
    ui.requests[0].resolve(kind === "tts" ? wavResponse() : textResponse("first"));
    await work;
    const oldUrl = e[`${kind}-download`].href;
    work = ui.submit(kind);
    assert.equal(e[`${kind}-result`].hidden, true);
    assert.equal(e[`${kind}-download`].href, undefined);
    assert.deepEqual(ui.revoked, [oldUrl]);
    ui.requests[1].resolve(errorResponse());
    await work;
    assert.equal(e[`${kind}-error`].textContent, "Service unavailable");
    assert.equal(e[`${kind}-error`].hidden, false);
    assert.equal(e[`${kind}-result`].hidden, true);
    assert.equal(e["tts-generate"].disabled, false);
    assert.equal(e["stt-transcribe"].disabled, false);
    work = ui.submit(kind);
    ui.requests[2].resolve(kind === "tts" ? wavResponse() : textResponse("retry"));
    await work;
    assert.equal(e[`${kind}-error`].hidden, true);
    assert.equal(e[`${kind}-result`].hidden, false);
  }
});

test("network errors release both send controls", async () => {
  const ui = setup();
  const work = ui.submit("tts");
  ui.requests[0].reject(new TypeError("mock network failure"));
  await work;
  assert.equal(ui.elements["tts-error"].hidden, false);
  assert.equal(ui.elements["tts-result"].hidden, true);
  assert.equal(ui.elements["tts-generate"].disabled, false);
  assert.equal(ui.elements["stt-transcribe"].disabled, false);
});
