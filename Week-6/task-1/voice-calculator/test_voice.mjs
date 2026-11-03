import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { parseVoiceCommand } from "./static/voice-command.mjs";
import { StreamingPcm16, pcmLittleEndian } from "./static/pcm-resampler.mjs";
import { makeWav } from "./static/voice-audio.mjs";

test("four operations, decimal, digits, punctuation and is", () => {
    for (const [text, left, operation, right] of [
        ["five plus two is", "5", "add", "2"],
        ["seven minus three is", "7", "subtract", "3"],
        ["three times two is", "3", "multiply", "2"],
        ["nine over three is", "9", "divide", "3"],
        ["one point five plus two is", "1.5", "add", "2"],
        ["5.5 PLUS 2 IS!", "5.5", "add", "2"],
        ["Five, plus two. Is!", "5", "add", "2"],
        ["zero point five plus nine is", "0.5", "add", "9"],
        ["one two plus three is", "12", "add", "3"],
    ]) {
        const parsed = parseVoiceCommand(text);
        assert.deepEqual([parsed.left, parsed.operation, parsed.right], [left, operation, right]);
        assert.ok(parsed.normalized.endsWith(" ="));
    }
});

test("invalid words and sequences are rejected in full", () => {
    for (const text of ["", null, "five please plus two is", "five plus two", "is five plus two",
        "five plus two is is", "five plus is", "plus two is", "five plus two minus one is",
        "point five plus two is", "five point point two plus one is", "five plus two is hello",
        "constructor plus two is", "5.5 2 plus one is", "one hundred plus two is",
        "-6 + 2 is", "−6 plus 2 is", "6 + -2 is", "6--2=", "6 - -2 is",
        "6 + 2 - 1 is", "6 - 2 is =", "6 - 2 equals", "6 please - 2 is",
        "6 - 2 is unknown", "6 ** 2 is", ".5 + 2 is", "1..5 + 2 is", "1.5.2 + 2 is"]) {
        assert.throws(() => parseVoiceCommand(text), undefined, String(text));
    }
});

test("Azure operator symbols normalize to the existing word grammar", () => {
    for (const [text, expected] of [
        ["6 - 2 is.", ["6", "subtract", "2", "6 − 2 ="]],
        ["5 + 2 is.", ["5", "add", "2", "5 + 2 ="]],
        ["3 × 2 is.", ["3", "multiply", "2", "3 × 2 ="]],
        ["9 / 3 is.", ["9", "divide", "3", "9 ÷ 3 ="]],
        ["1.5 + 2 is.", ["1.5", "add", "2", "1.5 + 2 ="]],
        ["6−2=", ["6", "subtract", "2", "6 − 2 ="]],
        ["3*2=.", ["3", "multiply", "2", "3 × 2 ="]],
        ["9÷3=", ["9", "divide", "3", "9 ÷ 3 ="]],
        ["Five + two IS!", ["5", "add", "2", "5 + 2 ="]],
    ]) {
        const value = parseVoiceCommand(text);
        assert.deepEqual([value.left, value.operation, value.right, value.normalized], expected);
    }
});

test("real sample rates, duration, mono and block continuity", () => {
    for (const rate of [16000, 44100, 48000, 96000]) {
        const input = Float32Array.from({ length: rate }, (_, i) => Math.sin(2 * Math.PI * 1000 * i / rate));
        const whole = new StreamingPcm16(rate).push([input]);
        const converter = new StreamingPcm16(rate);
        const split = [];
        for (let at = 0; at < input.length; at += 127) split.push(...converter.push([input.subarray(at, at + 127)]));
        assert.equal(whole.length, 16000);
        assert.deepEqual(split, Array.from(whole));
        const power = whole.reduce((sum, value) => sum + value * value, 0) / 16000;
        assert.ok(power > 4e8); // Converted signal remains audio, not merely a changed header.
    }
    assert.deepEqual(Array.from(new StreamingPcm16(16000).push([Float32Array.of(1), Float32Array.of(-1)])), [0]);
    const bytes = new DataView(pcmLittleEndian(Int16Array.of(-32768, 32767)));
    assert.equal(bytes.getUint8(0), 0); assert.equal(bytes.getUint8(1), 128);
});

test("WAV carries correct RIFF lengths and 16kHz 16bit mono samples", () => {
    const wav = makeWav([pcmLittleEndian(Int16Array.of(1, -2)), pcmLittleEndian(Int16Array.of(3))]);
    const v = new DataView(wav);
    assert.equal(new TextDecoder().decode(wav.slice(0, 4)), "RIFF");
    assert.equal(v.getUint32(4, true), wav.byteLength - 8);
    assert.equal(v.getUint16(20, true), 1); assert.equal(v.getUint16(22, true), 1);
    assert.equal(v.getUint32(24, true), 16000); assert.equal(v.getUint16(34, true), 16);
    assert.equal(v.getUint32(40, true), 6); assert.equal(v.getInt16(46, true), -2);
    assert.throws(() => makeWav([]));
    assert.throws(() => makeWav([new ArrayBuffer(480002)]));
});

test("worklet sends silence to speakers, flushes tail and caps 15 seconds", () => {
    let Processor;
    const messages = [];
    class Base { constructor() { this.port = { postMessage: message => messages.push(message) }; } }
    const source = fs.readFileSync(new URL("./static/voice-worklet.mjs", import.meta.url), "utf8").replace(/^import .*;\r?\n/, "");
    vm.runInNewContext(source, { StreamingPcm16, pcmLittleEndian, sampleRate: 48000,
        AudioWorkletProcessor: Base, registerProcessor: (_name, cls) => { Processor = cls; } });
    const node = new Processor();
    const out = [new Float32Array(128).fill(1)];
    node.process([[new Float32Array(128).fill(0.5)]], [out]);
    assert.equal(messages.length, 0); assert.ok(out[0].every(value => value === 0));
    node.port.onmessage({ data: "start" });
    node.process([[new Float32Array(480).fill(0.5)]], [out]);
    node.port.onmessage({ data: "flush" });
    assert.equal(messages[0].buffer.byteLength, 320);
    assert.equal(messages.at(-1).type, "flushed");
    messages.length = 0;
    const capped = new Processor(); capped.port.onmessage({ data: "start" });
    for (let i = 0; i < 151; i++) capped.process([[new Float32Array(4800)]], [out]);
    assert.equal(messages.filter(message => message.type === "pcm").reduce((sum, m) => sum + m.buffer.byteLength, 0), 480000);
    assert.equal(messages.filter(message => message.type === "flushed").length, 1);
});
