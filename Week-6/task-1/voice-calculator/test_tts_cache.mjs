import test from "node:test";
import assert from "node:assert/strict";
import { TtsAudioCache } from "./static/tts-cache.mjs";
import { SpeechQueue } from "./static/tts-queue.mjs";

const blob = () => new Blob([new Uint8Array(64)]);
const settle = async () => { for (let i = 0; i < 12; i++) await new Promise(resolve => setImmediate(resolve)); };
function deferred() { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; }

test("all fixed key sounds are reused; dynamic results are not retained", async () => {
    let calls = 0;
    const cache = new TtsAudioCache(async () => { calls++; return blob(); });
    for (const text of "zero one two three four five six seven eight nine point plus minus times over".split(" ")) {
        const first = await cache.get(text);
        assert.equal(await cache.get(text), first);
    }
    assert.equal(calls, 15); assert.equal(cache.cache.size, 15);
    await cache.get("is eight"); await cache.get("is eight");
    assert.equal(calls, 17); assert.equal(cache.cache.size, 15);
    assert.equal(cache.stats.hits, 15);
});

test("same in-flight text shares a promise; different texts use at most one HTTP request", async () => {
    const pending = deferred(); let calls = 0;
    const cache = new TtsAudioCache(async () => { calls++; if (calls === 1) return pending.promise; return blob(); });
    const one = cache.get("five"), same = cache.get("five"), second = cache.get("six");
    assert.equal(one, same); assert.equal(calls, 1); assert.equal(cache.stats.shared, 1);
    pending.resolve(blob()); await Promise.all([one, same, second]); assert.equal(calls, 2);
});

test("cancellation rejects pending work; late audio is not cached; successful cache survives", async () => {
    const pending = deferred(); let calls = 0;
    const cache = new TtsAudioCache(async () => { calls++; return calls === 2 ? pending.promise : blob(); });
    const ready = await cache.get("five");
    const waiting = cache.get("six"); const canceled = assert.rejects(waiting, { name: "AbortError" });
    cache.cancel(); await canceled;
    pending.resolve(blob()); await settle();
    assert.equal(cache.cache.has("six"), false);
    assert.equal(await cache.get("five"), ready); assert.equal(calls, 2);
    await cache.get("six"); assert.equal(calls, 3);
});

test("failures are retried and cache bytes/pending work remain bounded", async () => {
    let calls = 0;
    const cache = new TtsAudioCache(async () => { if (++calls === 1) throw new Error("failed"); return blob(); }, { maxBytes: 64 });
    await assert.rejects(cache.get("five")); await cache.get("five"); await cache.get("six");
    assert.equal(cache.bytes, 64); assert.equal(cache.cache.size, 1);
    const pending = deferred();
    const bounded = new TtsAudioCache(() => pending.promise, { maxPending: 1 });
    const first = bounded.get("five");
    await assert.rejects(bounded.get("six"), /queue full/);
    pending.resolve(blob()); await first;
});

test("request and playback queue times contain numeric durations without text", async () => {
    let clock = 0; const measurements = [], audios = [], request = deferred();
    const q = new SpeechQueue({
        fetchAudio: () => request.promise, now: () => clock,
        createAudio: () => { const audio = { play: async () => {}, pause() {}, removeAttribute() {}, load() {} }; audios.push(audio); return audio; },
        createURL: () => "blob:test", revokeURL() {}, onError() {},
        setTimer: () => 1, clearTimer() {}, onMetrics: metrics => measurements.push(metrics),
    });
    q.setEnabled(true); q.key("5"); clock = 10; q.key("6"); clock = 40;
    request.resolve(blob()); await settle();
    assert.deepEqual(measurements[0], { requestWaitMs: 40, playbackQueueMs: 0 });
    clock = 100; audios[0].onended(); await settle();
    assert.deepEqual(measurements[1], { requestWaitMs: 0, playbackQueueMs: 90 });
    assert.deepEqual(Object.keys(measurements[1]).sort(), ["playbackQueueMs", "requestWaitMs"]);
    q.cancel(); await settle();
});

test("cached playback preserves order and cancellation prevents old audio", async () => {
    let requests = 0;
    const cache = new TtsAudioCache(async () => { requests++; return blob(); });
    const played = [], audios = [];
    const q = new SpeechQueue({
        fetchAudio: (text, signal) => cache.get(text, signal), onCancel: () => cache.cancel(),
        createURL: value => value, revokeURL() {}, onError() {}, setTimer: () => 1, clearTimer() {},
        createAudio: () => { const audio = { play: async () => { played.push(audios.length); }, pause() {}, removeAttribute() {}, load() {} }; audios.push(audio); return audio; },
    });
    q.setEnabled(true); q.key("5"); q.key("5"); await settle();
    assert.equal(requests, 1); assert.equal(played.length, 1);
    audios[0].onended(); await settle(); assert.equal(requests, 1); assert.equal(played.length, 2);
    q.setMicrophoneBusy(true); q.key("5"); await settle(); assert.equal(played.length, 2);
    q.setMicrophoneBusy(false); q.key("5"); await settle(); assert.equal(played.length, 3); assert.equal(requests, 1);
    q.setEnabled(false); await settle();
    q.setEnabled(true); q.key("5"); q.cancel(); await settle();
    assert.equal(played.length, 3); assert.equal(requests, 1);
});
