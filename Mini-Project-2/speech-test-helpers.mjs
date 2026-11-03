import {makeWav} from './static/voice-audio.mjs';
export const speechReply = () => ({ok: true, headers: new Headers({'Content-Type': 'audio/wav'}),
    blob: async () => new Blob([makeWav([new ArrayBuffer(320)])], {type: 'audio/wav'})});

export function mockSpeech({fetchReply, playError, autoEnd = true} = {}) {
    const state = {requests: [], audios: [], urls: [], revoked: [], timers: new Map(), plays: 0};
    let number = 0;
    const env = {
        fetch: async (url, options) => {
            state.requests.push({url, options});
            return fetchReply ? fetchReply(url, options) : speechReply();
        },
        createURL: () => { const url = 'blob:mock-' + state.urls.length; state.urls.push(url); return url; },
        revokeURL: url => state.revoked.push(url),
        createAudio: url => {
            const audio = {url, paused: false, removed: false, loaded: false,
                play() {
                    state.plays++;
                    if (playError) return Promise.reject(Object.assign(new Error('blocked'), {name: 'NotAllowedError'}));
                    if (autoEnd) queueMicrotask(() => audio.onended?.());
                    return Promise.resolve();
                },
                pause() { this.paused = true; }, removeAttribute() { this.removed = true; }, load() { this.loaded = true; },
            };
            state.audios.push(audio); return audio;
        },
        setTimer: (fn, ms) => { const id = ++number; state.timers.set(id, {fn, ms}); return id; },
        clearTimer: id => state.timers.delete(id), onPageHide: fn => { state.pageHide = fn; },
    };
    state.fire = ms => { for (const [id, timer] of [...state.timers]) if (timer.ms === ms) {state.timers.delete(id); timer.fn();} };
    return {env, state};
}
