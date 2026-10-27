// Offline DOM/media mocks: never requests real microphone access or a network.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { parseVoiceCommand } from "./static/voice-command.mjs";

let sequence = 0;
async function harness({ denied = false, recognized = "five plus two is", apiFailure = false, voiceFailure = false, resultValue = 7, calculationGate } = {}) {
    class Element {
        constructor() { this.listeners = {}; this.dataset = {}; this.disabled = false; this.textContent = ""; }
        addEventListener(name, callback) { this.listeners[name] = callback; }
        setAttribute() {}
    }
    const nodes = Object.fromEntries(["display", "error", "voice-start", "voice-stop", "voice-status", "voice-error", "voice-transcript", "voice-command"].map(id => ["#" + id, new Element()]));
    const keypad = [new Element()]; keypad[0].dataset = { digit: "1" };
    const listeners = {};
    const document = { querySelector: id => nodes[id], querySelectorAll: selector => selector === "[data-operation]" ? [] : keypad,
        addEventListener: (event, callback) => { listeners[event] = callback; } };
    const timers = new Map(); let timerId = 0;
    const setTimeout = (callback, ms) => { timers.set(++timerId, { callback, ms }); return timerId; };
    const clearTimeout = id => timers.delete(id);
    const requests = [];
    const calculation = { resultValue, apiFailure };
    const fetch = async (url, options) => {
        requests.push({ url, options });
        if (url === "/api/voice-input") return { ok: !voiceFailure, json: async () => voiceFailure ? { error: "Azure bağlantısı kurulamadı." } : { text: recognized } };
        if (calculationGate) await calculationGate;
        return { ok: !calculation.apiFailure, json: async () => calculation.apiFailure ? { error: "Sıfıra bölme yapılamaz." } : { result: calculation.resultValue } };
    };
    const track = { stopped: false, stop() { this.stopped = true; } };
    const resources = { track };
    class Context {
        constructor() { this.state = "running"; this.sampleRate = 48000; this.destination = {}; this.audioWorklet = { addModule: async () => {} }; resources.context = this; }
        createMediaStreamSource() { return { connect() {}, disconnect() {} }; }
        async resume() {}
        async close() { this.state = "closed"; }
    }
    class Node {
        constructor() {
            resources.node = this;
            this.port = { close() {}, postMessage: data => {
                if (data === "flush") queueMicrotask(() => this.port.onmessage?.({ data: { type: "flushed" } }));
            } };
        }
        connect() {} disconnect() {}
    }
    const window = { AudioContext: Context, AudioWorkletNode: Node, addEventListener: (event, callback) => { listeners[event] = callback; } };
    vm.runInNewContext(fs.readFileSync(new URL("./static/script.js", import.meta.url), "utf8"), { document, window, fetch });
    Object.assign(globalThis, { window, document, AudioContext: Context, AudioWorkletNode: Node, fetch, setTimeout, clearTimeout });
    Object.defineProperty(globalThis, "navigator", { configurable: true, value: { mediaDevices: { getUserMedia: async () => {
        if (denied) throw Object.assign(new Error(), { name: "NotAllowedError" });
        return { getTracks: () => [track] };
    } } } });
    await import(`./static/voice-input.mjs?test=${++sequence}`);
    const settle = async () => { for (let i = 0; i < 20; i++) await new Promise(resolve => setImmediate(resolve)); };
    const pcm = () => resources.node.port.onmessage({ data: { type: "pcm", buffer: new ArrayBuffer(320) } });
    return { nodes, requests, keypad, resources, listeners, timers, settle, pcm, window, calculation };
}

test("voice validates first, uses shared calculator API and releases media", async () => {
    const h = await harness();
    await h.nodes["#voice-start"].listeners.click();
    assert.ok(h.nodes["#voice-start"].disabled); assert.ok(h.keypad[0].disabled);
    h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
    assert.deepEqual(h.requests.map(r => r.url), ["/api/voice-input", "/api/calculate"]);
    assert.deepEqual(JSON.parse(h.requests[1].options.body), { operation: "add", x: 5, y: 2 });
    assert.equal(h.nodes["#display"].textContent, "7");
    assert.equal(h.nodes["#voice-command"].textContent, "5 + 2 = 7");
    assert.ok(h.resources.track.stopped); assert.equal(h.resources.context.state, "closed");
    assert.equal(h.nodes["#voice-start"].disabled, false);
});

test("unsupported command preserves calculator state and permits retry", async () => {
    const h = await harness({ recognized: "five please plus two is" });
    h.keypad[0].listeners.click(); assert.equal(h.nodes["#display"].textContent, "1");
    await h.nodes["#voice-start"].listeners.click(); h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
    assert.equal(h.requests.length, 1);
    assert.equal(h.nodes["#display"].textContent, "1");
    assert.equal(h.nodes["#voice-transcript"].textContent, "five please plus two is");
    assert.equal(h.nodes["#voice-command"].textContent, ""); assert.equal(h.nodes["#voice-error"].hidden, false);
    await h.nodes["#voice-start"].listeners.click(); assert.equal(h.nodes["#voice-start"].disabled, true);
    h.listeners.pagehide(); await h.settle();
});

test("permission rejection, page exit and automatic stop release controls", async () => {
    let h = await harness({ denied: true });
    await h.nodes["#voice-start"].listeners.click();
    assert.equal(h.nodes["#voice-start"].disabled, false); assert.equal(h.requests.length, 0);
    h = await harness(); await h.nodes["#voice-start"].listeners.click();
    h.listeners.pagehide(); await h.settle();
    assert.ok(h.resources.track.stopped); assert.equal(h.resources.context.state, "closed"); assert.equal(h.requests.length, 0);
    h = await harness(); await h.nodes["#voice-start"].listeners.click(); h.pcm();
    [...h.timers.values()].find(timer => timer.ms === 15000).callback(); await h.settle();
    assert.equal(h.nodes["#voice-start"].disabled, false); assert.ok(h.resources.track.stopped);
});

test("division by zero uses existing error path and unlocks controls", async () => {
    const h = await harness({ recognized: "five over zero is", apiFailure: true });
    await h.nodes["#voice-start"].listeners.click(); h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
    assert.deepEqual(JSON.parse(h.requests[1].options.body), { operation: "divide", x: 5, y: 0 });
    assert.equal(h.nodes["#error"].textContent, "Sıfıra bölme yapılamaz.");
    assert.equal(h.nodes["#voice-start"].disabled, false);
});

test("all five required command examples go through the keypad calculation path", async () => {
    for (const [text, operation, x, y] of [
        ["five plus two is", "add", 5, 2], ["seven minus three is", "subtract", 7, 3],
        ["three times two is", "multiply", 3, 2], ["nine over three is", "divide", 9, 3],
        ["one point five plus two is", "add", 1.5, 2],
    ]) {
        const h = await harness(); await h.window.calculatorVoice.apply(parseVoiceCommand(text));
        assert.deepEqual(JSON.parse(h.requests[0].options.body), { operation, x, y });
    }
});

test("service failure and disconnected microphone release resources and allow retry", async () => {
    let h = await harness({ voiceFailure: true });
    await h.nodes["#voice-start"].listeners.click(); h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
    assert.equal(h.requests.length, 1); assert.equal(h.nodes["#display"].textContent, "0");
    assert.equal(h.nodes["#voice-error"].textContent, "Azure bağlantısı kurulamadı.");
    assert.equal(h.nodes["#voice-start"].disabled, false);
    assert.ok(h.resources.track.stopped); assert.equal(h.resources.context.state, "closed");
    h = await harness(); await h.nodes["#voice-start"].listeners.click();
    h.resources.track.onended(); await h.settle();
    assert.equal(h.nodes["#voice-start"].disabled, false); assert.equal(h.requests.length, 0);
    assert.equal(h.resources.context.state, "closed");
});

test("missing worklet flush times out without uploading partial audio", async () => {
    const h = await harness(); await h.nodes["#voice-start"].listeners.click(); h.pcm();
    h.resources.node.port.postMessage = () => {};
    h.nodes["#voice-stop"].listeners.click();
    [...h.timers.values()].find(timer => timer.ms === 3000).callback(); await h.settle();
    assert.equal(h.requests.length, 0); assert.ok(h.resources.track.stopped);
    assert.equal(h.nodes["#voice-start"].disabled, false); assert.equal(h.nodes["#voice-error"].hidden, false);
});

test("symbol transcripts use the shared API and display its result", async () => {
    for (const [recognized, operation, x, y, resultValue, normalized] of [
        ["6 - 2 is.", "subtract", 6, 2, 4, "6 − 2 ="],
        ["5 + 2 is.", "add", 5, 2, 7, "5 + 2 ="],
        ["3 × 2 is.", "multiply", 3, 2, 6, "3 × 2 ="],
        ["9 / 3 is.", "divide", 9, 3, 3, "9 ÷ 3 ="],
        ["1.5 + 2 is.", "add", 1.5, 2, 3.5, "1.5 + 2 ="],
    ]) {
        const h = await harness({ recognized, resultValue });
        await h.nodes["#voice-start"].listeners.click(); h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
        assert.deepEqual(JSON.parse(h.requests[1].options.body), { operation, x, y });
        assert.equal(h.nodes["#display"].textContent, String(resultValue));
        assert.equal(h.nodes["#voice-command"].textContent, `${normalized} ${resultValue}`);
        assert.equal(h.nodes["#voice-transcript"].textContent, recognized);
    }
});

test("voice result waits for the successful API response and displays its value", async () => {
    let resolve;
    const calculationGate = new Promise(done => { resolve = done; });
    const h = await harness({ recognized: "4 * 6 is.", resultValue: 24, calculationGate });
    await h.nodes["#voice-start"].listeners.click(); h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
    assert.equal(h.nodes["#voice-command"].textContent, "4 × 6 =");
    assert.equal(h.nodes["#voice-status"].textContent, "İşleniyor…");
    assert.equal(h.nodes["#voice-start"].disabled, true);
    resolve(); await h.settle();
    assert.equal(h.nodes["#voice-transcript"].textContent, "4 * 6 is.");
    assert.equal(h.nodes["#voice-command"].textContent, "4 × 6 = 24");
    assert.equal(h.nodes["#voice-status"].textContent, "İşlem tamamlandı.");
    assert.equal(h.requests.filter(request => request.url === "/api/calculate").length, 1);

    // A deliberately different mock value proves the UI uses the API response.
    h.calculation.resultValue = 99;
    await h.nodes["#voice-start"].listeners.click(); h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
    assert.equal(h.nodes["#voice-command"].textContent, "4 × 6 = 99");

    h.calculation.apiFailure = true;
    await h.nodes["#voice-start"].listeners.click();
    assert.equal(h.nodes["#voice-command"].textContent, "");
    h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
    assert.equal(h.nodes["#voice-command"].textContent, "");
    assert.equal(h.nodes["#voice-status"].textContent, "Hata");
    assert.equal(h.nodes["#voice-error"].hidden, false);
    assert.equal(h.nodes["#voice-transcript"].textContent, "4 * 6 is.");
});

test("zero is displayed as a successful voice calculation result", async () => {
    const h = await harness({ recognized: "2 - 2 is.", resultValue: 0 });
    await h.nodes["#voice-start"].listeners.click(); h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
    assert.equal(h.nodes["#voice-command"].textContent, "2 − 2 = 0");
    assert.equal(h.nodes["#voice-status"].textContent, "İşlem tamamlandı.");
});

test("voice capture blocks output before microphone permission is requested", async () => {
    const h = await harness();
    let blocked = false;
    const events = [];
    h.window.calculatorAudio = {
        setMicrophoneBusy(value) { blocked = value; events.push(value); }, cancel() {},
        key() { assert.fail("Programmatic voice must not speak keys"); },
        result() { assert.fail("Programmatic voice must not speak results"); },
    };
    const original = navigator.mediaDevices.getUserMedia;
    navigator.mediaDevices.getUserMedia = async (...args) => { assert.equal(blocked, true); return original(...args); };
    await h.nodes["#voice-start"].listeners.click(); h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
    assert.deepEqual(events, [true, false]);
});

test("invalid symbol sequences preserve the previous calculator state", async () => {
    for (const recognized of ["-6 + 2 is.", "6 - -2 is.", "6 + 2 - 1 is.", "6 unknown - 2 is."]) {
        const h = await harness({ recognized });
        h.keypad[0].listeners.click();
        await h.nodes["#voice-start"].listeners.click(); h.pcm(); h.nodes["#voice-stop"].listeners.click(); await h.settle();
        assert.equal(h.requests.length, 1);
        assert.equal(h.nodes["#display"].textContent, "1");
        assert.equal(h.nodes["#voice-error"].hidden, false);
        assert.equal(h.nodes["#voice-start"].disabled, false);
    }
});
