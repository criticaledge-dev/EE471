"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const { pathToFileURL } = require("node:url");

async function engine() {
  return import(pathToFileURL(path.join(__dirname, "../static/pcm-resampler.mjs")).href);
}

test("resampling preserves duration and block continuity at actual browser rates", async () => {
  const { StreamingPcm16 } = await engine();
  for (const rate of [16000, 44100, 48000, 96000]) {
    const input = Float32Array.from({ length: rate }, (_, i) => Math.sin(2 * Math.PI * 1000 * i / rate) * .5);
    const whole = new StreamingPcm16(rate).push([input]);
    const resampler = new StreamingPcm16(rate);
    const chunks = [];
    let offset = 0;
    for (const size of [1, 127, 5, 257, 13, 1024]) {
      chunks.push(...resampler.push([input.subarray(offset, offset + size)]));
      offset += size;
    }
    while (offset < input.length) {
      chunks.push(...resampler.push([input.subarray(offset, offset + 128)]));
      offset += 128;
    }
    assert.equal(whole.length, 16000, `one second at ${rate} must produce one second at 16 kHz`);
    assert.deepEqual(Int16Array.from(chunks), whole);
    // Sample rate was actually converted, preserving the 1 kHz waveform.
    const correlation = whole.reduce((sum, sample, i) => sum + sample * Math.sin(2 * Math.PI * 1000 * (i + .5) / 16000), 0);
    assert.ok(correlation > 100000000);
  }
});

test("mono downmix, clipping, signed 16-bit little endian and sub-sample tail", async () => {
  const { StreamingPcm16, pcmLittleEndian } = await engine();
  const pcm = new StreamingPcm16(16000).push([Float32Array.from([1, -1, .5]), Float32Array.from([-1, 1, .5])]);
  assert.deepEqual([...pcm], [0, 0, 16384]);
  const bytes = new Uint8Array(pcmLittleEndian(Int16Array.from([-32768, 32767, 1])));
  assert.deepEqual([...bytes], [0, 128, 255, 127, 1, 0]);
  const resampler = new StreamingPcm16(48000);
  assert.equal(resampler.push([Float32Array.from([1, 1])]).length, 0);
  assert.deepEqual([...resampler.push([Float32Array.from([1])])], [32767]);
  assert.throws(() => new StreamingPcm16(0));
});

async function worklet(rate = 48000) {
  const { StreamingPcm16, pcmLittleEndian } = await engine();
  let Processor;
  const sent = [];
  class Base {
    constructor() { this.port = { postMessage: message => sent.push(message) }; }
  }
  const source = fs.readFileSync(path.join(__dirname, "../static/pcm-worklet.mjs"), "utf8").replace(/^import .*;\s*/, "");
  vm.runInNewContext(source, { StreamingPcm16, pcmLittleEndian, sampleRate: rate,
    AudioWorkletProcessor: Base, registerProcessor: (_name, processor) => { Processor = processor; } });
  const processor = new Processor();
  return { processor, sent, message: type => processor.port.onmessage({ data: { type } }) };
}

test("worklet sends no PCM before ready, silences local output and flushes tail in order", async () => {
  const { processor, sent, message } = await worklet();
  const output = [[new Float32Array(128).fill(1)]];
  processor.process([[new Float32Array(128).fill(.25)]], output);
  assert.equal(sent.length, 0);
  assert.ok(output[0][0].every(sample => sample === 0));
  message("start");
  for (let i = 0; i < 40; i++) processor.process([[new Float32Array(128).fill(.25)]], output);
  assert.equal(sent[0].type, "pcm");
  assert.equal(sent[0].pcm.byteLength, 3200);
  message("flush");
  assert.deepEqual(sent.map(item => item.type), ["pcm", "pcm", "flushed"]);
  const samples = sent.filter(item => item.type === "pcm").reduce((sum, item) => sum + item.pcm.byteLength / 2, 0);
  assert.equal(samples, Math.floor(40 * 128 / 3));
  assert.ok(sent.filter(item => item.type === "pcm").every(item => item.pcm.byteLength <= 3200));
});

test("worklet bounds outstanding packets and enforces the 60 second sample cap", async () => {
  let fixture = await worklet(16000);
  fixture.message("start");
  for (let i = 0; i < 100; i++) fixture.processor.process([[new Float32Array(128)]], [[new Float32Array(128)]]);
  assert.equal(fixture.sent.filter(item => item.type === "pcm").length, 4);
  assert.equal(fixture.sent.filter(item => item.type === "error").length, 1);
  fixture = await worklet(16000);
  fixture.message("start");
  let acknowledged = 0;
  for (let i = 0; i < 7600 && !fixture.processor.finished; i++) {
    fixture.processor.process([[new Float32Array(128)]], [[new Float32Array(128)]]);
    while (acknowledged < fixture.sent.filter(item => item.type === "pcm").length) {
      acknowledged++;
      fixture.message("credit");
    }
  }
  assert.equal(fixture.sent.filter(item => item.type === "pcm").reduce((sum, item) => sum + item.pcm.byteLength, 0), 1920000);
  assert.equal(fixture.sent.at(-1).type, "flushed");
});
