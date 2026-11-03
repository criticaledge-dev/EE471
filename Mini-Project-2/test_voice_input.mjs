import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { LibraryMicrophone } from "./static/voice-input.mjs";
import { StreamingPcm16, pcmLittleEndian } from "./static/pcm-resampler.mjs";
import { makeWav } from "./static/voice-audio.mjs";
import { mockVoiceEnvironment, deferred, settle } from "./voice-test-helpers.mjs";

function setup(options = {}) {
    const {env, state} = mockVoiceEnvironment(options);
    const calls = [], statuses = [], transcripts = [], controls = [];
    let releases = 0;
    const microphone = new LibraryMicrophone({environment: env, acquire: () => ({}), release() { releases++; },
        runCommandText: async (text, options) => { calls.push({text, options}); return {ok: true}; },
        onState: (message, error) => statuses.push({message, error}), onTranscript: text => transcripts.push(text),
        onControls: value => controls.push(value),
    });
    return {microphone, state, calls, statuses, transcripts, controls, releases: () => releases};
}

test("denied microphone permission is separate and controls recover", async () => {
    const s = setup({denied: true}); await s.microphone.start();
    assert.equal(s.microphone.current, null); assert.equal(s.releases(), 1);
    assert.match(s.statuses.at(-1).message, /permission was denied/);
    assert.equal(s.statuses.at(-1).error, true); assert.equal(s.calls.length, 0);
    assert.equal(s.controls.at(-1).startDisabled, false);
});

test("stop waits for final PCM and sends matching WAV before invoking one shared command", async () => {
    const s = setup({autoFlush: false}); await s.microphone.start();
    s.state.emit({type: "pcm", buffer: new ArrayBuffer(100)}); s.microphone.stop();
    await settle(); assert.equal(s.state.fetches.length, 0);
    s.state.emit({type: "pcm", buffer: new ArrayBuffer(200)});
    s.state.emit({type: "flushed"}); s.state.emit({type: "flushed"}); await settle();
    assert.equal(s.state.fetches.length, 1); assert.equal(s.calls.length, 1);
    const file = s.state.fetches[0].options.body.get("audio"), buffer = await file.arrayBuffer();
    const view = new DataView(buffer);
    assert.equal(buffer.byteLength, 344); assert.equal(view.getUint32(40, true), 300);
    assert.equal(view.getUint32(24, true), 16000); assert.equal(view.getUint16(22, true), 1); assert.equal(view.getUint16(34, true), 16);
    assert.equal(s.calls[0].text, "List books");
    assert.ok(s.state.track.stopped); assert.equal(s.state.contexts[0].state, "closed");
    assert.ok(s.state.nodes[0].port.closed); assert.equal(s.releases(), 1);
});

test("30 second automatic stop flushes tail; missing flush times out without upload", async () => {
    let s = setup(); await s.microphone.start(); s.state.fireTimer(30000); await settle();
    assert.equal(s.state.fetches.length, 1); assert.equal(s.calls.length, 1); assert.ok(s.state.track.stopped);
    s = setup({autoFlush: false}); await s.microphone.start(); s.microphone.stop(); s.state.fireTimer(3000); await settle();
    assert.equal(s.state.fetches.length, 0); assert.equal(s.calls.length, 0);
    assert.match(s.statuses.at(-1).message, /Incomplete audio was not sent/); assert.ok(s.state.track.stopped);
});

test("canceled permission request stops late tracks and does not start a session", async () => {
    const permission = deferred(), s = setup({permission});
    const started = s.microphone.start(); await s.microphone.cancel();
    permission.resolve(s.state.stream); await started;
    assert.ok(s.state.track.stopped); assert.equal(s.state.contexts.length, 0); assert.equal(s.calls.length, 0);
});

test("cancel/page exit and request timeout ignore late transcript without executing", async () => {
    for (const action of [s => s.microphone.cancel(), s => s.state.pageHide(), s => s.state.fireTimer(90000)]) {
        const pending = deferred(), s = setup({fetchReply: () => pending.promise});
        await s.microphone.start(); s.microphone.stop(); await settle();
        await action(s); await settle();
        pending.resolve({ok: true, json: async () => ({text: "Delete item four", language: "en-US"})}); await settle();
        assert.equal(s.calls.length, 0); assert.equal(s.microphone.current, null);
        assert.ok(s.state.fetches[0].options.signal.aborted); assert.ok(s.state.track.stopped);
    }
});

test("STT failure never calls command parser/runner; transcript stays unmodified on success", async () => {
    let s = setup({fetchReply: async () => ({ok: false, json: async () => ({error: "Speech service unavailable"})})});
    await s.microphone.start(); s.microphone.stop(); await settle();
    assert.equal(s.calls.length, 0); assert.match(s.statuses.at(-1).message, /Speech recognition:/);
    const text = 'Create item, type book, title "1984", author Test Author, pages 220.';
    s = setup({fetchReply: async () => ({ok: true, json: async () => ({text, language: "en-US"})})});
    await s.microphone.start(); s.microphone.stop(); await settle();
    assert.equal(s.calls[0].text, text); assert.equal(s.transcripts.at(-1), text);
});

test("second start is blocked; cleanup attempts all resources even if one fails", async () => {
    const s = setup(); await s.microphone.start(); await s.microphone.start();
    assert.equal(s.state.contexts.length, 1);
    s.state.nodes[0].disconnect = () => { throw new Error("private"); };
    await s.microphone.cancel();
    assert.ok(s.state.track.stopped); assert.equal(s.state.contexts[0].state, "closed");
    assert.equal(s.microphone.current, null); assert.equal(s.releases(), 1);
    assert.match(s.statuses.at(-1).message, /cleanup failed/);
});

test("actual sample rates preserve PCM duration and continuity; WAV caps at 30 seconds", () => {
    for (const rate of [16000, 44100, 48000, 96000]) {
        const input = Float32Array.from({length: rate}, (_, i) => Math.sin(2 * Math.PI * 1000 * i / rate));
        const whole = new StreamingPcm16(rate).push([input]);
        const converter = new StreamingPcm16(rate), split = [];
        for (let at = 0; at < input.length; at += 127) split.push(...converter.push([input.subarray(at, at + 127)]));
        assert.equal(whole.length, 16000); assert.deepEqual(split, Array.from(whole));
    }
    assert.equal(makeWav([new ArrayBuffer(960000)]).byteLength, 960044);
    assert.throws(() => makeWav([new ArrayBuffer(960002)]));
    assert.throws(() => makeWav([]));
    const view = new DataView(pcmLittleEndian(Int16Array.of(-32768, 32767)));
    assert.equal(view.getUint8(1), 128); assert.equal(view.getInt16(2, true), 32767);
});

test("real worklet caps PCM at 480000 samples, outputs silence and flushes once", () => {
    let Processor; const messages = [];
    class Base { constructor() { this.port = {postMessage: data => messages.push(data)}; } }
    const source = fs.readFileSync(new URL("./static/voice-worklet.mjs", import.meta.url), "utf8").replace(/^import .*;\r?\n/, "");
    vm.runInNewContext(source, {AudioWorkletProcessor: Base, StreamingPcm16, pcmLittleEndian, sampleRate: 48000,
        registerProcessor: (_name, value) => { Processor = value; }});
    const processor = new Processor(), output = [[new Float32Array(128).fill(1)]];
    processor.process([[new Float32Array(128)]], output); assert.equal(messages.length, 0);
    assert.ok(output[0][0].every(value => value === 0));
    processor.port.onmessage({data: "start"});
    for (let i = 0; i < 301; i++) processor.process([[new Float32Array(4800)]], output);
    assert.equal(messages.filter(m => m.type === "pcm").reduce((sum, m) => sum + m.buffer.byteLength, 0), 960000);
    assert.equal(messages.filter(m => m.type === "flushed").length, 1);
});
