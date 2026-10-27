import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { SpeechQueue, buttonWords, resultWords } from "./static/tts-queue.mjs";
import { readTtsResponse } from "./static/tts-response.mjs";
import { makeWav } from "./static/voice-audio.mjs";

const validBlob = () => new Blob([makeWav([new ArrayBuffer(320)])], { type: "audio/wav" });

const settle = async () => { for (let i = 0; i < 12; i++) await new Promise(resolve => setImmediate(resolve)); };
function deferred() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
function fixture(options = {}) {
    const requests = [], played = [], revoked = [], errors = [], audios = [], statuses = [];
    const q = new SpeechQueue({
        fetchAudio: async (text, signal) => { requests.push({ text, signal }); return options.fetchAudio ? options.fetchAudio(text, signal) : {}; },
        createURL: () => "blob:" + audios.length, revokeURL: url => revoked.push(url), onError: message => errors.push(message), onStatus: message => statuses.push(message),
        createAudio: url => {
            const audio = { play() { played.push(url); return options.playError ? Promise.reject(options.playError) : Promise.resolve(); }, pause() { this.paused = true; },
                removeAttribute() {}, load() {}, onended: null, onerror: null };
            audios.push(audio); return audio;
        }, setTimer: () => 1, clearTimer() {}, maxItems: options.maxItems || 12,
    });
    q.setEnabled(true);
    return { q, requests, played, revoked, errors, audios, statuses };
}

test("button vocabulary and numeric result policy", () => {
    assert.deepEqual(Object.values(buttonWords), ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "point", "plus", "minus", "times", "over"]);
    for (const [value, words] of [[8, "is eight"], [0, "is zero"], [-24.05, "is minus twenty four point zero five"],
        [1234, "is one thousand two hundred thirty four"], [1e21, "is one times ten to the power of twenty one"],
        [1e-7, "is one times ten to the power of minus seven"]]) assert.equal(resultWords(value), words);
    for (const value of [Infinity, NaN, "oops", "1+2"]) assert.throws(() => resultWords(value));
});

test("queue serializes generation and playback in press order", async () => {
    const f = fixture(); f.q.key("5"); f.q.key("add"); f.q.key("3"); f.q.result(8, f.q.ticket());
    await settle(); assert.deepEqual(f.requests.map(r => r.text), ["five"]); assert.equal(f.played.length, 1);
    for (const expected of ["plus", "three", "is eight"]) {
        f.audios.at(-1).onended(); await settle(); assert.equal(f.requests.at(-1).text, expected);
    }
    f.audios.at(-1).onended(); await settle(); assert.equal(f.revoked.length, 4); assert.equal(f.q.running, false);
});

test("timer functions are invoked without a queue receiver like native Window timers", async () => {
    let requested = false;
    const q = new SpeechQueue({
        fetchAudio: async () => { requested = true; return {}; },
        createURL: () => 'blob:timer', revokeURL() {}, onError() {},
        createAudio: () => ({ play() { queueMicrotask(() => this.onended()); return Promise.resolve(); }, pause() {}, removeAttribute() {}, load() {} }),
        setTimer: function () { assert.equal(this, undefined, 'Window timer received SpeechQueue as this'); return 1; },
        clearTimer: function () { assert.equal(this, undefined, 'Window clearTimer received SpeechQueue as this'); },
    });
    q.setEnabled(true); q.key('5'); await settle();
    assert.equal(requested, true); assert.equal(q.running, false); assert.equal(q.active, null);
});

test("new enqueues do not overwrite the active consumer's request status", async () => {
    const pending = deferred(), f = fixture({ fetchAudio: () => pending.promise });
    f.q.key('5'); f.q.key('6');
    assert.match(f.statuses.at(-1), /Flask.*ses isteniyor/);
    f.q.cancel(); pending.resolve({}); await settle();
});

test("consumer setup errors are caught and do not leave running/active stuck", async () => {
    const errors = [];
    const q = new SpeechQueue({ fetchAudio: () => assert.fail('request must not start'),
        createAudio() {}, createURL() {}, revokeURL() {}, onError: message => errors.push(message),
        setTimer() { throw new TypeError('private timer failure'); }, clearTimer() {},
    });
    q.setEnabled(true); q.key('5'); await settle();
    assert.equal(q.running, false); assert.equal(q.active, null); assert.equal(q.items.length, 0);
    assert.match(errors.at(-1), /Flask bağlantısını/); assert.doesNotMatch(errors.at(-1), /private/);
});

test("bounded queue never grows past its limit", async () => {
    const pending = deferred(); const f = fixture({ fetchAudio: () => pending.promise, maxItems: 3 });
    for (let i = 0; i < 100; i++) f.q.key("1");
    assert.equal(f.q.items.length, 2); assert.match(f.errors.at(-1), /kuyruğu dolu/);
    f.q.cancel(); pending.resolve({}); await settle(); assert.equal(f.played.length, 0);
});

test("clear, disable, microphone and page-exit cancellation discard late responses", async () => {
    for (const action of [q => q.cancel(), q => q.setEnabled(false), q => q.setMicrophoneBusy(true)]) {
        const pending = deferred(); const f = fixture({ fetchAudio: () => pending.promise });
        const ticket = f.q.ticket(); f.q.key("1"); f.q.key("2"); action(f.q);
        pending.resolve({}); await settle(); f.q.result(8, ticket);
        assert.equal(f.played.length, 0); assert.equal(f.q.items.length, 0); assert.equal(f.requests[0].signal.aborted, true);
    }
});

test("active playback is stopped and URLs released before microphone recording", async () => {
    const f = fixture(); f.q.key("1"); await settle();
    f.q.setMicrophoneBusy(true); f.q.key("2"); f.q.result(8, f.q.ticket()); await settle();
    assert.equal(f.audios[0].paused, true); assert.equal(f.revoked.length, 1); assert.equal(f.requests.length, 1);
    f.q.setMicrophoneBusy(false); f.q.key("3"); await settle(); assert.equal(f.requests.at(-1).text, "three");
    f.q.cancel(); await settle();
});

test("TTS failure reports separately and queue recovers", async () => {
    let fail = true;
    const f = fixture({ fetchAudio: async () => { if (fail) throw new Error("native"); return {}; } });
    f.q.key("1"); await settle(); assert.match(f.errors.at(-1), /hesaplama sonucu korunuyor/);
    fail = false; f.q.key("2"); await settle(); assert.equal(f.played.length, 1);
    f.q.cancel(); await settle();
});

function calculatorFixture() {
    const els = Object.fromEntries(["display", "error", "voice-start"].map(id => ["#" + id, { textContent: "", setAttribute() {} }]));
    const buttons = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "add", "subtract", "multiply", "divide", "equals", "clear"].map(key => ({
        key, dataset: key === "equals" || key === "clear" ? { action: key } : Object.hasOwn(buttonWords, key) && key.length === 1 ? { digit: key } : { operation: key },
        addEventListener(_event, callback) { this.click = callback; }, setAttribute() {},
    }));
    const pending = deferred(); const calls = [], spoken = [], mic = [];
    const audio = { key: value => spoken.push(value), ticket: () => 1, result: (value, ticket) => spoken.push([value, ticket]),
        cancel: () => spoken.push("cancel"), setMicrophoneBusy: value => mic.push(value) };
    const window = { calculatorAudio: audio };
    vm.runInNewContext(fs.readFileSync(new URL("./static/script.js", import.meta.url), "utf8"), {
        window, document: { querySelector: id => els[id], querySelectorAll: selector => selector === "[data-operation]" ? [] : buttons, addEventListener() {} },
        fetch: async (url, options) => { calls.push({ url, options }); return pending.promise; },
    });
    return { click: key => buttons.find(b => b.key === key).click(), els, pending, calls, spoken, window, mic };
}

test("physical equals waits for the single API response; failures never request result speech", async () => {
    for (const success of [true, false]) {
        const f = calculatorFixture(); f.click("5"); f.click("add"); f.click("3"); f.click("equals");
        assert.deepEqual(f.spoken, ["5", "add", "3"]); assert.equal(f.calls.length, 1);
        f.pending.resolve({ ok: success, json: async () => success ? { result: 8 } : { error: "calculation failed" } });
        await settle(); assert.equal(f.calls.length, 1);
        assert.deepEqual(f.spoken, success ? ["5", "add", "3", ["8", 1]] : ["5", "add", "3"]);
        if (success) assert.equal(resultWords(f.spoken.at(-1)[0]), "is eight");
    }
});

test("all physical buttons have speech hooks; clear cancels; programmatic voice has none", async () => {
    for (const key of Object.keys(buttonWords)) {
        const f = calculatorFixture(); f.click(key); assert.deepEqual(f.spoken, [key]);
    }
    const f = calculatorFixture(); f.click("clear"); assert.deepEqual(f.spoken, ["cancel"]);
    f.window.calculatorVoice.setBusy(true); assert.deepEqual(f.mic, [true]);
    const applied = f.window.calculatorVoice.apply({ left: "5", operation: "add", right: "3" });
    f.pending.resolve({ ok: true, json: async () => ({ result: 8 }) }); await applied;
    assert.deepEqual(f.spoken, ["cancel", "cancel"]); // clear only, no key/result speech.
});

test("browser adapter uses own backend, visible toggle and page-exit cancellation", async () => {
    const handlers = {}, toggle = { checked: false, addEventListener: (event, handler) => { handlers[event] = handler; } };
    const error = {}, status = {}, window = { addEventListener: (event, handler) => { handlers[event] = handler; } };
    const requests = [], audios = [], revoked = [];
    class Audio {
        constructor(url) { this.url = url; audios.push(this); }
        play() { return Promise.resolve(); } pause() { this.paused = true; } removeAttribute() {} load() {}
    }
    let fail = false;
    Object.assign(globalThis, { window, Audio,
        document: { querySelector: selector => selector === "#tts-enabled" ? toggle : selector === "#tts-status" ? status : selector === "#tts-metrics" ? null : error },
        fetch: async (url, options) => { requests.push({ url, options }); return {
            ok: !fail, status: fail ? 502 : 200, headers: { get: () => "audio/wav" }, blob: async () => validBlob() }; },
    });
    const savedCreate = URL.createObjectURL, savedRevoke = URL.revokeObjectURL;
    URL.createObjectURL = () => "blob:test"; URL.revokeObjectURL = url => revoked.push(url);
    try {
        await import("./static/tts-output.mjs?adapter-test");
        window.calculatorAudio.key("1"); assert.equal(requests.length, 0);
        toggle.checked = true; handlers.change(); window.calculatorAudio.key("1"); await settle();
        assert.equal(requests[0].url, "/api/tts"); assert.deepEqual(JSON.parse(requests[0].options.body), { text: "one" });
        assert.equal(audios.length, 1);
        assert.match(status.textContent, /oynatmasını başlattı/);
        toggle.checked = false; handlers.change(); await settle(); assert.ok(audios[0].paused); assert.deepEqual(revoked, ["blob:test"]);
        toggle.checked = true; handlers.change(); fail = true; window.calculatorAudio.key("2"); await settle();
        assert.equal(error.hidden, false); assert.match(error.textContent, /hesaplama sonucu korunuyor/);
        fail = false; window.calculatorAudio.key("3"); await settle(); handlers.pagehide(); await settle();
        assert.equal(toggle.checked, false); assert.equal(window.calculatorAudio.enabled, false); assert.ok(audios.at(-1).paused);
    } finally { window.calculatorAudio.cancel(); URL.createObjectURL = savedCreate; URL.revokeObjectURL = savedRevoke; }
});

test("restored checked toggle initializes queue without requiring a change event", async () => {
    const toggle = { checked: true, addEventListener() {} }, error = {}, status = {};
    const window = { addEventListener() {} };
    const pending = deferred(); let requests = 0;
    Object.assign(globalThis, { window,
        document: { querySelector: selector => selector === "#tts-enabled" ? toggle : selector === "#tts-status" ? status : selector === "#tts-metrics" ? null : error },
        fetch: async () => { requests++; return pending.promise; },
    });
    await import("./static/tts-output.mjs?restored-checkbox-test");
    assert.equal(window.calculatorAudio.enabled, true);
    assert.match(status.textContent, /açık/);
    window.calculatorAudio.key("1"); assert.equal(requests, 1);
    assert.match(status.textContent, /Flask.*ses isteniyor/);
    window.calculatorAudio.cancel();
    pending.resolve({ ok: true, headers: { get: () => "audio/wav" }, blob: async () => validBlob() });
    await settle();
});

test("HTTP and nonempty PCM WAV validation identify the response stage safely", async () => {
    const response = blob => ({ ok: true, headers: { get: () => "audio/wav" }, blob: async () => blob });
    assert.equal((await readTtsResponse(response(validBlob()))).size, 364);
    for (const blob of [new Blob([]), new Blob(["not WAV"]), new Blob([new ArrayBuffer(64)]),
        new Blob([makeWav([new ArrayBuffer(320)]).slice(0, 44)])]) {
        await assert.rejects(readTtsResponse(response(blob)), error => error.outputCode === "audio");
    }
    await assert.rejects(readTtsResponse({ ok: false, status: 503 }), error => error.outputCode === "http" && error.httpStatus === 503);
    await assert.rejects(readTtsResponse({ ok: true, headers: { get: () => "text/html" } }), error => error.outputCode === "audio");
});

test("request failures and play rejection expose distinct safe diagnostics", async () => {
    for (const [failure, pattern] of [
        [Object.assign(new Error("private"), { outputCode: "http", httpStatus: 503 }), /HTTP 503.*yapılandırması eksik/],
        [Object.assign(new Error("private"), { outputCode: "audio" }), /boş veya geçerli PCM WAV/],
        [Object.assign(new Error("private"), { name: "AbortError" }), /20 saniyede/],
        [new TypeError("private"), /Flask bağlantısını/],
    ]) {
        const f = fixture({ fetchAudio: async () => { throw failure; } });
        f.q.key("1"); await settle(); assert.match(f.errors.at(-1), pattern);
        assert.equal(f.played.length, 0); assert.doesNotMatch(f.errors.at(-1), /private/);
    }
    const f = fixture({ playError: Object.assign(new Error("private URL"), { name: "NotAllowedError" }) });
    f.q.key("1"); await settle();
    assert.match(f.errors.at(-1), /audio.play\(\).*NotAllowedError/);
    assert.doesNotMatch(f.errors.at(-1), /private URL/); assert.equal(f.revoked.length, 1);
    assert.equal(f.statuses.at(-1), "Sesli çıkış hatası.");
});

test("physical DOM button traverses enabled adapter, queue, WAV response and play", async () => {
    const toggle = { checked: false, addEventListener(_event, handler) { this.change = handler; } };
    const elements = Object.fromEntries(["tts-error", "tts-status", "tts-metrics", "display", "error", "voice-start"].map(id => ["#" + id, { textContent: "", setAttribute() {} }]));
    elements["#tts-enabled"] = toggle;
    const button = { dataset: { digit: "5" }, addEventListener(_event, handler) { this.click = handler; } };
    const document = { querySelector: selector => elements[selector], querySelectorAll: selector => selector === "[data-operation]" ? [] : [button], addEventListener() {} };
    const window = { addEventListener() {} }, requests = [], audios = [];
    class Audio {
        constructor() { audios.push(this); } play() { this.started = true; return Promise.resolve(); }
        pause() {} removeAttribute() {} load() {}
    }
    const fetch = async (url, options) => { requests.push({ url, options }); return {
        ok: true, headers: { get: () => "audio/wav" }, blob: async () => validBlob() }; };
    Object.assign(globalThis, { document, window, Audio, fetch });
    const create = URL.createObjectURL, revoke = URL.revokeObjectURL;
    URL.createObjectURL = () => "blob:integration"; URL.revokeObjectURL = () => {};
    try {
        await import("./static/tts-output.mjs?physical-button-integration");
        vm.runInNewContext(fs.readFileSync(new URL("./static/script.js", import.meta.url), "utf8"), { document, window, fetch });
        toggle.checked = true; toggle.change(); button.click(); await settle();
        assert.equal(elements["#display"].textContent, "5");
        assert.equal(requests.length, 1); assert.equal(requests[0].url, "/api/tts");
        assert.deepEqual(JSON.parse(requests[0].options.body), { text: "five" });
        assert.equal(audios[0].started, true);
        assert.match(elements["#tts-status"].textContent, /oynatmasını başlattı/);
        audios[0].onended(); await settle();
        assert.match(elements["#tts-status"].textContent, /tamamladı/);
    } finally { window.calculatorAudio.cancel(); URL.createObjectURL = create; URL.revokeObjectURL = revoke; }
});
