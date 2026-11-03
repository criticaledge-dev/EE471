import test from 'node:test';
import assert from 'node:assert/strict';
import {SpokenResponses} from './static/spoken-responses.mjs';
import {mockSpeech, speechReply} from './speech-test-helpers.mjs';
import {settle, deferred} from './voice-test-helpers.mjs';

function setup(options) {
    const {env, state} = mockSpeech(options); const changes = [];
    const output = new SpokenResponses({environment: env, onChange: s => changes.push(s)});
    return {env, state, changes, output};
}
test('silent default, bounded sequential queue and visible last response', async () => {
    const s = setup({autoEnd: false});
    s.output.notify('silent result'); assert.equal(s.state.requests.length, 0);
    assert.equal(s.changes.at(-1).text, 'silent result');
    s.output.setEnabled(true);
    for (const text of ['one', 'two', 'three', 'four']) s.output.notify(text);
    await settle(); assert.equal(s.state.requests.length, 1); assert.equal(s.state.plays, 1);
    assert.match(s.changes.find(c => c.error)?.error, /queue full/);
    s.state.audios[0].onended(); await settle();
    assert.equal(s.state.requests.length, 2); assert.equal(s.state.plays, 2);
    s.state.audios[1].onended(); await settle(); s.state.audios[2].onended(); await settle();
    assert.deepEqual(s.state.requests.map(r => JSON.parse(r.options.body).text), ['one', 'two', 'three']);
    assert.equal(s.state.revoked.length, 3); assert.equal(s.state.timers.size, 0);
    assert.ok(s.state.audios.every(a => a.paused && a.loaded && a.removed && a.onended === null && a.onerror === null));
});
test('off/on discards late TTS and the next response still plays without manual drain', async () => {
    const pending = deferred(); let calls = 0;
    const s = setup({fetchReply: () => ++calls === 1 ? pending.promise : speechReply()});
    s.output.setEnabled(true); s.output.notify('old'); await settle();
    s.output.setEnabled(false); s.output.setEnabled(true); s.output.notify('new'); await settle();
    assert.equal(s.state.requests[0].options.signal.aborted, true);
    assert.equal(s.state.plays, 1); pending.resolve(speechReply()); await settle();
    assert.equal(s.state.plays, 1); assert.equal(s.state.urls.length, 1);
});
test('microphone cancels active audio, defers new result until release and prevents late playback', async () => {
    const s = setup({autoEnd: false}); s.output.setEnabled(true); s.output.notify('old'); await settle();
    s.output.setMicrophone(true); assert.ok(s.state.audios[0].paused);
    s.output.notify('voice result'); await settle(); assert.equal(s.state.requests.length, 1);
    s.output.setMicrophone(false); await settle(); assert.equal(s.state.requests.length, 2);
    assert.equal(s.state.plays, 2); s.output.stop(); await settle();
    const pending = deferred(), late = setup({fetchReply: () => pending.promise});
    late.output.setEnabled(true); late.output.notify('old'); late.output.setMicrophone(true);
    pending.resolve(speechReply()); await settle(); assert.equal(late.state.plays, 0);
    late.output.setMicrophone(false); await settle(); assert.equal(late.state.plays, 0);
});
test('play rejection is reported; replay uses only the latest text', async () => {
    const s = setup({playError: true}); s.output.setEnabled(true); s.output.notify('result', 'Refresh warning.');
    await settle(); assert.match(s.changes.at(-1).error, /playback was rejected/);
    assert.equal(s.changes.at(-1).canPlay, true); s.output.replay(); await settle();
    assert.equal(s.state.requests.length, 2);
    assert.equal(JSON.parse(s.state.requests[1].options.body).text, 'result Refresh warning.');
    assert.equal(s.state.revoked.length, 2);
});
test('HTTP, invalid MIME, empty or malformed WAV do not play', async () => {
    for (const reply of [{ok: false}, {...speechReply(), headers: new Headers({'Content-Type': 'application/json'})},
        {...speechReply(), blob: async () => new Blob([])}, {...speechReply(), blob: async () => new Blob(['x'.repeat(100)])}]) {
        const s = setup({fetchReply: () => reply}); s.output.setEnabled(true); s.output.notify('result');
        await settle(); assert.equal(s.state.plays, 0); assert.ok(s.changes.at(-1).error);
    }
});
test('request/playback timeouts, stop and pagehide clean resources and ignore obsolete notifications', async () => {
    const pending = deferred(), s = setup({fetchReply: () => pending.promise});
    s.output.setEnabled(true); s.output.notify('result'); await settle(); s.state.fire(40000); await settle();
    assert.ok(s.changes.at(-1).error); assert.equal(s.output.running, false);
    const p = setup({autoEnd: false}); p.output.setEnabled(true); p.output.notify('result'); await settle();
    p.state.fire(180000); await settle(); assert.ok(p.changes.at(-1).error); assert.equal(p.state.revoked.length, 1);
    p.output.notify('again'); await settle(); p.state.pageHide(); await settle();
    assert.equal(p.state.timers.size, 0); assert.equal(p.state.revoked.length, 2);
    p.output.notify('late'); assert.equal(p.state.requests.length, 2);
    const old = s.output.generation; s.output.stop(); s.output.notify('late command', '', old);
    pending.resolve(speechReply()); await settle(); assert.equal(s.state.plays, 0);
});
