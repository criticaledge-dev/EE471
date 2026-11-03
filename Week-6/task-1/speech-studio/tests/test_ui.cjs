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
    "stt-download", "stt-copy", "translation-form", "translation-submit",
    "translation-source", "translation-target", "translation-status",
    "translation-error", "translation-result", "translation-original", "translation-text",
    "pronunciation-form", "pronunciation-submit", "pronunciation-status", "pronunciation-error",
    "pronunciation-result", "pronunciation-reference-result", "pronunciation-scope", "pronunciation-segments",
    "diarization-start"];
  const elements = Object.fromEntries(ids.map(id => [id, {
    textContent: "", hidden: false, disabled: false, value: "", children: [],
    addEventListener(name, callback) { this[name] = callback; },
    setAttribute(name, value) { this[name] = value; },
    removeAttribute(name) { delete this[name]; },
    pause() {}, load() {},
    appendChild(child) { this.children.push(child); return child; },
    replaceChildren() { this.children = []; },
  }]));
  elements["tts-text"].value = "Hello world";
  elements["tts-language"].value = "en-US";
  const requests = [], revoked = [], copied = [], urls = [];
  const unload = [];
  const context = {
    document: { createElement: tag => ({ tagName: tag, textContent: "", children: [],
      appendChild(child) { this.children.push(child); return child; } }), getElementById: id => {
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

test("translation uses the shared guard, renders literal texts and allows retry after failure", async () => {
  const ui = setup(), e = ui.elements;
  let work = ui.submit("translation");
  for (const id of ["tts-generate", "stt-transcribe", "translation-submit"]) {
    assert.equal(e[id].disabled, true);
  }
  await ui.submit("tts");
  await ui.submit("stt");
  await ui.submit("translation");
  assert.equal(ui.requests.length, 1);
  assert.equal(ui.requests[0].url, "/api/translate");
  assert.equal(ui.requests[0].options.body.form, e["translation-form"]);
  ui.requests[0].resolve({ ok: true, json: async () => ({
    recognized_text: "<b>Hello</b>", translated_text: "<b>Merhaba</b>",
    source_language: "en-US", target_language: "tr",
  }) });
  await work;
  assert.equal(e["translation-original"].textContent, "<b>Hello</b>");
  assert.equal(e["translation-text"].textContent, "<b>Merhaba</b>");
  assert.equal(e["translation-result"].hidden, false);
  work = ui.submit("translation");
  assert.equal(e["translation-original"].textContent, "");
  assert.equal(e["translation-text"].textContent, "");
  assert.equal(e["translation-result"].hidden, true);
  ui.requests[1].resolve(errorResponse());
  await work;
  assert.equal(e["translation-error"].hidden, false);
  assert.equal(e["translation-result"].hidden, true);
  for (const id of ["tts-generate", "stt-transcribe", "translation-submit"]) {
    assert.equal(e[id].disabled, false);
  }
  work = ui.submit("translation");
  ui.requests[2].resolve({ ok: true, json: async () => ({ recognized_text: "Hello", translated_text: "Merhaba" }) });
  await work;
  assert.equal(e["translation-error"].hidden, true);
  assert.equal(e["translation-result"].hidden, false);
  e["translation-source"].value = "tr-TR";
  e["translation-source"].change();
  assert.equal(e["translation-target"].value, "en");
  work = ui.submit("tts");
  await ui.submit("translation");
  assert.equal(ui.requests.length, 4);
  ui.requests[3].resolve(wavResponse());
  await work;
  assert.equal(e["translation-original"].textContent, "Hello");
});

test("translation rejects incomplete success and releases controls after a network failure", async () => {
  const ui = setup(), e = ui.elements;
  let work = ui.submit("translation");
  ui.requests[0].resolve({ ok: true, json: async () => ({ recognized_text: "Hello" }) });
  await work;
  assert.equal(e["translation-result"].hidden, true);
  assert.equal(e["translation-error"].hidden, false);
  work = ui.submit("translation");
  ui.requests[1].reject(new TypeError("mock network failure"));
  await work;
  assert.equal(e["translation-result"].hidden, true);
  assert.equal(e["translation-error"].hidden, false);
  assert.equal(e["translation-submit"].disabled, false);
  assert.equal(e["tts-generate"].disabled, false);
  assert.equal(e["stt-transcribe"].disabled, false);
});

test("pronunciation renders named segment scores/word table safely and permits retry", async () => {
  const ui = setup(), e = ui.elements;
  const buttons = ["tts-generate", "stt-transcribe", "translation-submit", "pronunciation-submit"];
  const fixture = {
    reference_text: "<b>Reference</b>", session_complete: true, assessment_complete: false,
    score_scale: 100, scope: "segments_only", overall_scores: null,
    warnings: ["Fixture warning"], segments: [{ index: 1, text: "<script>literal</script>",
      scores: { accuracy: 90, fluency: 80, completeness: null, pronunciation: 85 },
      words: [{ word: "<img>", accuracy: null, error_type: "None" }],
    }, { index: 2, text: "Second", scores: { accuracy: 70 }, words: [] }],
  };
  let work = ui.submit("pronunciation");
  for (const id of buttons) assert.equal(e[id].disabled, true);
  for (const kind of ["tts", "stt", "translation", "pronunciation"]) await ui.submit(kind);
  assert.equal(ui.requests.length, 1);
  assert.equal(ui.requests[0].url, "/api/pronunciation");
  assert.equal(ui.requests[0].options.body.form, e["pronunciation-form"]);
  ui.requests[0].resolve({ ok: true, json: async () => fixture });
  await work;
  assert.equal(e["pronunciation-reference-result"].textContent, "<b>Reference</b>");
  assert.equal(e["pronunciation-result"].hidden, false);
  assert.equal(e["pronunciation-segments"].children.length, 2);
  const all = [];
  function visit(node) { all.push(node); for (const child of node.children || []) visit(child); }
  visit(e["pronunciation-segments"]);
  const texts = all.map(node => node.textContent);
  assert.ok(texts.includes("<script>literal</script>"));
  assert.ok(texts.includes("<img>"));
  assert.ok(texts.includes("Accuracy: 90 / 100"));
  assert.ok(texts.includes("Completeness: Azure tarafından döndürülmedi"));
  assert.ok(all.some(node => node.tagName === "table"));
  assert.ok(e["pronunciation-scope"].textContent.includes("Değerlendirme eksik"));
  for (const id of buttons) assert.equal(e[id].disabled, false);
  work = ui.submit("pronunciation");
  assert.equal(e["pronunciation-result"].hidden, true);
  assert.equal(e["pronunciation-segments"].children.length, 0);
  ui.requests[1].resolve(errorResponse());
  await work;
  assert.equal(e["pronunciation-error"].hidden, false);
  assert.equal(e["pronunciation-result"].hidden, true);
  for (const id of buttons) assert.equal(e[id].disabled, false);
  work = ui.submit("pronunciation");
  ui.requests[2].resolve({ ok: true, json: async () => fixture });
  await work;
  assert.equal(e["pronunciation-result"].hidden, false);
  assert.equal(e["pronunciation-error"].hidden, true);
  work = ui.submit("tts");
  await ui.submit("pronunciation");
  assert.equal(ui.requests.length, 4);
  ui.requests[3].resolve(wavResponse());
  await work;
});

test("pronunciation cannot show a noncompleted session as success", async () => {
  const ui = setup(), e = ui.elements;
  const work = ui.submit("pronunciation");
  ui.requests[0].resolve({ ok: true, json: async () => ({ session_complete: false, segments: [] }) });
  await work;
  assert.equal(e["pronunciation-error"].hidden, false);
  assert.equal(e["pronunciation-result"].hidden, true);
  assert.equal(e["pronunciation-submit"].disabled, false);
});
