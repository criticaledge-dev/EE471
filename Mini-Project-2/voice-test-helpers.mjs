// Offline media fixtures; never access a real microphone or network.
export const settle = async () => { for (let i = 0; i < 20; i++) await new Promise(resolve => setImmediate(resolve)); };
export function deferred() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
export function mockVoiceEnvironment({ autoFlush = true, denied = false, permission, fetchReply } = {}) {
    let timerId = 0;
    const state = { timers: new Map(), fetches: [], nodes: [], contexts: [], pageHide: null };
    state.track = { stopped: false, stop() { this.stopped = true; } };
    state.stream = { getTracks: () => [state.track] };
    const env = {
        async getMedia() {
            if (denied) throw Object.assign(new Error("private"), { name: "NotAllowedError" });
            return permission ? permission.promise : state.stream;
        },
        createContext() {
            const context = { sampleRate: 48000, state: "running", destination: {}, audioWorklet: { async addModule() {} },
                async resume() {}, async close() { this.state = "closed"; },
                createMediaStreamSource() { state.source = { connect() {}, disconnect() { this.disconnected = true; } }; return state.source; } };
            state.contexts.push(context); return context;
        },
        createNode() {
            const node = { connect() {}, disconnect() { this.disconnected = true; } };
            node.port = { close() { this.closed = true; }, postMessage(data) {
                if (data === "flush" && autoFlush) queueMicrotask(() => {
                    node.port.onmessage?.({data: {type: "pcm", buffer: new ArrayBuffer(320)}});
                    node.port.onmessage?.({data: {type: "flushed"}});
                });
            } };
            state.nodes.push(node); return node;
        },
        async fetch(url, options) {
            state.fetches.push({url, options});
            if (fetchReply) return fetchReply(url, options);
            return {ok: true, json: async () => ({text: "List books", language: "en-US"})};
        },
        setTimer(fn, ms) { state.timers.set(++timerId, {fn, ms}); return timerId; },
        clearTimer(id) { state.timers.delete(id); },
        onPageHide(fn) { state.pageHide = fn; },
    };
    state.emit = data => state.nodes.at(-1).port.onmessage?.({data});
    state.fireTimer = ms => [...state.timers.values()].find(timer => timer.ms === ms)?.fn();
    return {env, state};
}
