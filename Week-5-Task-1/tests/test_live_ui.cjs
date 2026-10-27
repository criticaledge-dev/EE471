"use strict";
// No browser, microphone or Azure is accessed: these are lifecycle mocks.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function setup(permissionError = false) {
  const element = () => ({ textContent: "", hidden: false, disabled: false, children: [], value: "en-US",
    addEventListener(name, fn) { this[name] = fn; },
    appendChild(child) { this.children.push(child); }, replaceChildren() { this.children = []; } });
  const ids = ["diarization-start", "diarization-stop", "diarization-language", "diarization-status", "diarization-error", "diarization-interim", "diarization-finals"];
  const elements = Object.fromEntries(ids.map(id => [id, element()]));
  const state = { busy: false, trackStopped: false, contextClosed: false, connected: false, ports: [], socket: null, node: null, timers: new Map(), now: 0 };
  const track = { stop() { state.trackStopped = true; }, addEventListener() {}, removeEventListener() {} };
  class Context {
    constructor() { this.state = "running"; this.sampleRate = 44100; this.audioWorklet = { async addModule() {} }; this.destination = {}; }
    createMediaStreamSource() { return { connect() { state.connected = true; }, disconnect() { state.connected = false; } }; }
    async resume() {}
    async close() { this.state = "closed"; state.contextClosed = true; }
  }
  class Node {
    constructor() {
      state.node = this;
      this.port = { postMessage(message) { state.ports.push(message); }, close() {} };
    }
    connect() {} disconnect() {}
  }
  class WS {
    static OPEN = 1;
    constructor(url) { state.socket = this; this.url = url; this.readyState = 1; this.bufferedAmount = 0; this.sent = []; }
    send(data) { this.sent.push(data); }
    close() { this.readyState = 3; }
  }
  const context = vm.createContext({
    document: { getElementById: id => elements[id], createElement: element },
    window: { addEventListener(name, callback) { state[name] = callback; } },
    navigator: { mediaDevices: { async getUserMedia() {
      if (permissionError) throw Object.assign(new Error(), { name: "NotAllowedError" });
      return { getTracks: () => [track] };
    } } },
    AudioContext: Context, AudioWorkletNode: Node, WebSocket: WS,
    location: { protocol: "http:", host: "localhost:5000" },
    setTimeout(fn, delay) { const id = ++state.now; state.timers.set(id, { fn, delay }); return id; },
    clearTimeout(id) { state.timers.delete(id); },
    setSpeechBusy(value) { state.busy = value; elements["diarization-start"].disabled = value; },
  });
  vm.runInContext("let speechBusy = false;", context);
  const setBusy = context.setSpeechBusy;
  context.setSpeechBusy = value => { vm.runInContext(`speechBusy = ${value}`, context); setBusy(value); };
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../static/diarization.js"), "utf8"), context);
  return { elements, state,
    start: () => elements["diarization-start"].click(),
    server: message => state.socket.onmessage({ data: JSON.stringify(message) }),
    worklet: message => state.node.port.onmessage({ data: message }) };
}

async function settle() { await new Promise(resolve => setImmediate(resolve)); }

test("permission precedes socket; ready precedes PCM; stop flush precedes stop command", async () => {
  const ui = setup(), { state, elements: e } = ui;
  await ui.start();
  state.socket.onopen();
  assert.equal(JSON.parse(state.socket.sent[0]).type, "start");
  assert.equal(state.connected, false);
  assert.equal(state.ports.length, 0);
  ui.server({ type: "ready", sample_rate: 16000, channels: 1, bits_per_sample: 16 });
  assert.equal(state.connected, true);
  assert.equal(state.ports[0].type, "start");
  ui.worklet({ type: "pcm", pcm: new ArrayBuffer(3200) });
  ui.server({ type: "interim", speaker_id: "Unknown", text: "<i>literal</i>" });
  assert.ok(e["diarization-interim"].textContent.includes("Unknown"));
  const final = { type: "final", result_id: "one", speaker_id: "Guest-1", text: "<script>literal</script>", offset_ms: 1000, duration_ms: 500 };
  ui.server(final);
  ui.server(final);
  assert.equal(e["diarization-finals"].children.length, 1); // visible before Stop
  assert.equal(e["diarization-finals"].children[0].children.at(-1).textContent, final.text);
  e["diarization-stop"].click();
  assert.equal(state.ports.at(-1).type, "flush");
  assert.equal(state.socket.sent.filter(value => typeof value === "string").length, 1);
  ui.worklet({ type: "pcm", pcm: new ArrayBuffer(200) });
  ui.worklet({ type: "flushed" });
  assert.equal(JSON.parse(state.socket.sent.at(-1)).type, "stop");
  assert.equal(state.busy, true); // no success before server completion
  ui.server({ ...final, result_id: "two", speaker_id: "Guest-2", text: "Last" });
  assert.equal(e["diarization-finals"].children.length, 2);
  ui.server({ type: "completed", final_count: 2 });
  await settle();
  assert.equal(state.busy, false);
  assert.equal(state.trackStopped, true);
  assert.equal(state.contextClosed, true);
  assert.equal(e["diarization-stop"].disabled, true);
  assert.ok(e["diarization-status"].textContent.includes("tamamlandı"));
});

test("permission denial, connection loss and page close reset resources and buttons", async () => {
  let ui = setup(true);
  await ui.start();
  await settle();
  assert.equal(ui.state.socket, null);
  assert.equal(ui.state.busy, false);
  assert.ok(ui.elements["diarization-error"].textContent.includes("izni"));
  ui = setup();
  await ui.start();
  ui.state.socket.onclose();
  await settle();
  assert.equal(ui.state.busy, false);
  assert.equal(ui.state.trackStopped, true);
  assert.equal(ui.state.contextClosed, true);
  await ui.start();
  ui.state.pagehide();
  await settle();
  assert.equal(ui.state.busy, false);
  assert.equal(ui.elements["diarization-start"].disabled, false);
});

test("duration stop and PCM backpressure are handled without claiming success", async () => {
  const ui = setup();
  await ui.start();
  ui.server({ type: "ready", sample_rate: 16000, channels: 1, bits_per_sample: 16 });
  const timer = [...ui.state.timers.values()].find(timer => timer.delay === 60000);
  timer.fn();
  assert.equal(ui.state.ports.at(-1).type, "flush");
  ui.state.socket.bufferedAmount = 100000;
  ui.worklet({ type: "pcm", pcm: new ArrayBuffer(3200) });
  await settle();
  assert.equal(ui.state.busy, false);
  assert.equal(ui.state.trackStopped, true);
  assert.ok(!ui.elements["diarization-status"].textContent.includes("Oturum tamamlandı"));
});
