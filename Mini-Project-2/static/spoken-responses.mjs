// Library-independent playback. No command parsing, mutations, or speechSynthesis.
export const speechEnvironment = () => ({
    fetch: (...args) => fetch(...args), createAudio: url => new Audio(url),
    createURL: blob => URL.createObjectURL(blob), revokeURL: url => URL.revokeObjectURL(url),
    setTimer: (fn, ms) => globalThis.setTimeout(fn, ms), clearTimer: id => globalThis.clearTimeout(id),
    onPageHide: fn => globalThis.addEventListener('pagehide', fn),
});

function abortable(promise, signal) {
    return new Promise((resolve, reject) => {
        const abort = () => reject(new Error('canceled'));
        if (signal.aborted) { abort(); return; }
        signal.addEventListener('abort', abort, {once: true});
        Promise.resolve(promise).then(resolve, reject).finally(() => signal.removeEventListener('abort', abort));
    });
}

export class SpokenResponses {
    constructor({environment = speechEnvironment(), onChange = () => {}, capacity = 3} = {}) {
        this.env = environment; this.onChange = onChange; this.capacity = capacity;
        this.enabled = false; this.microphone = false; this.disposed = false;
        this.generation = 0; this.items = []; this.active = null; this.running = false;
        this.lastText = ''; this.status = 'Spoken responses off.'; this.error = '';
        this.env.onPageHide(() => { this.disposed = true; this.enabled = false; this.cancel(); this.render(); });
        this.render();
    }
    render() { this.onChange({enabled: this.enabled, status: this.status, error: this.error, text: this.lastText,
        canPlay: this.enabled && !this.microphone && !this.disposed && Boolean(this.lastText)}); }
    cancel() {
        this.generation++; this.items = []; this.deferred = false;
        this.active?.controller.abort(); this.active?.finish?.(); this.clean(this.active);
    }
    clean(item) {
        if (!item) return;
        if (item.audio) {
            item.audio.onended = item.audio.onerror = null;
            item.audio.pause(); item.audio.removeAttribute('src'); item.audio.load(); item.audio = null;
        }
        if (item.url) { this.env.revokeURL(item.url); item.url = null; }
    }
    setEnabled(value) {
        if (this.disposed) return;
        this.enabled = Boolean(value); this.error = '';
        if (!this.enabled) this.cancel();
        this.status = !this.enabled ? 'Spoken responses off.' : this.microphone ? 'Speech paused for microphone processing.' : 'Spoken responses ready.'; this.render();
    }
    stop() { this.cancel(); this.error = ''; this.status = this.enabled ? 'Speech stopped.' : 'Spoken responses off.'; this.render(); }
    setMicrophone(value) {
        this.microphone = value;
        if (value) { this.cancel(); this.error = ''; this.status = 'Speech paused for microphone processing.'; }
        else this.status = this.enabled ? 'Spoken responses ready.' : 'Spoken responses off.';
        const pending = !value && this.deferred;
        this.deferred = false; this.render();
        if (pending && this.enabled) this.enqueue(this.lastText);
    }
    notify(text, warning = '', ticket = this.generation) {
        if (this.disposed || typeof text !== 'string' || !text.trim()) return;
        this.lastText = text + (warning ? ' ' + warning : ''); this.error = ''; this.render();
        if (!this.enabled || ticket !== this.generation) return;
        if (this.microphone) { this.deferred = true; return; }
        this.enqueue(this.lastText);
    }
    replay() {
        if (!this.enabled || this.microphone || this.disposed || !this.lastText) return;
        this.cancel(); this.enqueue(this.lastText); // Only TTS; never rerun the command.
    }
    enqueue(text) {
        if (this.items.length + (this.active ? 1 : 0) >= this.capacity) {
            this.error = 'Speech queue full. Use Play response for the latest result.'; this.render(); return;
        }
        this.items.push({text, generation: this.generation});
        void this.drain();
    }
    async drain() {
        if (this.running) return;
        this.running = true;
        try {
            while (this.items.length && this.enabled && !this.microphone && !this.disposed) {
                const item = this.items.shift(); this.active = item;
                item.controller = new AbortController();
                const current = () => item.generation === this.generation && this.enabled && !this.microphone && !this.disposed;
                let timer, stage = 'request';
                try {
                    this.error = ''; this.status = 'Preparing spoken response…'; this.render();
                    timer = this.env.setTimer(() => item.controller.abort(), 40000);
                    const response = await abortable(this.env.fetch('/api/tts', {method: 'POST',
                        headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text: item.text}),
                        signal: item.controller.signal}), item.controller.signal);
                    if (!current()) continue;
                    if (!response.ok) throw new Error('http'); // Do not display arbitrary server/SDK text.
                    const type = response.headers.get('Content-Type') || '';
                    if (!/^audio\/wav(?:;|$)/i.test(type)) throw new Error('audio');
                    const blob = await abortable(response.blob(), item.controller.signal);
                    if (!blob.size || blob.size > 16 * 1024 * 1024) throw new Error('audio');
                    const header = new Uint8Array(await abortable(blob.slice(0, 12).arrayBuffer(), item.controller.signal));
                    if (blob.size <= 44 || String.fromCharCode(...header.slice(0, 4)) !== 'RIFF'
                        || String.fromCharCode(...header.slice(8, 12)) !== 'WAVE') throw new Error('audio');
                    if (!current()) continue;
                    this.env.clearTimer(timer); stage = 'play';
                    item.url = this.env.createURL(blob); item.audio = this.env.createAudio(item.url);
                    await new Promise((resolve, reject) => {
                        item.finish = resolve;
                        item.audio.onended = resolve; item.audio.onerror = () => reject(new Error('media'));
                        timer = this.env.setTimer(() => reject(new Error('playback-timeout')), 180000);
                        Promise.resolve(item.audio.play()).then(() => {
                            if (current()) { this.status = 'Playing spoken response…'; this.render(); }
                        }).catch(reject);
                    });
                    if (current()) { this.status = 'Spoken response completed.'; this.render(); }
                } catch {
                    if (current()) {
                        this.status = 'Spoken response error.';
                        this.error = stage === 'play' ? 'Audio playback was rejected or failed. Use Play response to try again.'
                            : 'Speech could not be prepared. Check Speech configuration/connection, then use Play response.';
                        this.render();
                    }
                } finally {
                    if (timer !== undefined) this.env.clearTimer(timer);
                    this.clean(item); this.active = null;
                }
            }
        } finally { this.running = false; }
    }
}

export function mountSpokenResponses({document, environment}) {
    const toggle = document.getElementById('spoken-enabled');
    if (!toggle) return null;
    const play = document.getElementById('spoken-play'), stop = document.getElementById('spoken-stop');
    const output = new SpokenResponses({environment, onChange(state) {
        toggle.checked = state.enabled; play.disabled = !state.canPlay;
        document.getElementById('spoken-status').textContent = state.status;
        const error = document.getElementById('spoken-error'); error.textContent = state.error; error.hidden = !state.error;
        document.getElementById('spoken-text').textContent = state.text;
    }});
    toggle.checked = false; // Start silently even if the browser restores form controls.
    toggle.addEventListener('change', () => output.setEnabled(toggle.checked));
    play.addEventListener('click', () => output.replay()); stop.addEventListener('click', () => output.stop());
    return output;
}
