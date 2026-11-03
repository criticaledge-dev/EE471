const fixedWords = new Set("zero one two three four five six seven eight nine point plus minus times over".split(" "));
const aborted = () => Object.assign(new Error("canceled"), { name: "AbortError" });

// One HTTP request at a time, shared in-flight promises, fixed vocabulary only.
// Successful fixed audio survives cancellation; stale pending audio never does.
export class TtsAudioCache {
    constructor(fetchAudio, { onChange = () => {}, maxBytes = 2 * 1024 * 1024, maxPending = 12 } = {}) {
        Object.assign(this, { fetchAudio, onChange, maxBytes, maxPending });
        this.cache = new Map(); this.pending = new Map(); this.jobs = [];
        this.bytes = 0; this.running = false; this.generation = 0;
        this.stats = { hits: 0, shared: 0, requests: 0 };
    }
    get(text, signal) {
        if (signal?.aborted) return Promise.reject(aborted());
        if (this.cache.has(text)) {
            this.stats.hits++; this.onChange(); return Promise.resolve(this.cache.get(text));
        }
        if (this.pending.has(text)) {
            this.stats.shared++; this.onChange(); return this.pending.get(text).promise;
        }
        if (this.pending.size >= this.maxPending) return Promise.reject(new Error("audio preparation queue full"));
        const job = { text, generation: this.generation, controller: new AbortController() };
        job.promise = new Promise((resolve, reject) => { job.resolve = resolve; job.reject = reject; });
        // A caller belongs to this queue session: cancellation invalidates its shared job.
        job.abort = () => { job.controller.abort(); job.reject(aborted()); };
        job.signal = signal; signal?.addEventListener("abort", job.abort, { once: true });
        this.pending.set(text, job); this.jobs.push(job); void this.drain();
        return job.promise;
    }
    cancel() {
        this.generation++;
        for (const job of this.pending.values()) {
            job.abort(); job.signal?.removeEventListener("abort", job.abort);
        }
        this.jobs = []; this.pending.clear();
    }
    async drain() {
        if (this.running) return;
        this.running = true;
        try {
            while (this.jobs.length) {
                const job = this.jobs.shift();
                try {
                    if (job.controller.signal.aborted || job.generation !== this.generation) throw aborted();
                    this.stats.requests++; this.onChange();
                    const blob = await this.fetchAudio(job.text, job.controller.signal);
                    if (job.controller.signal.aborted || job.generation !== this.generation) throw aborted();
                    if (fixedWords.has(job.text) && blob.size > 0 && this.bytes + blob.size <= this.maxBytes) {
                        this.cache.set(job.text, blob); this.bytes += blob.size;
                    }
                    job.resolve(blob);
                } catch (error) { job.reject(error); }
                finally {
                    job.signal?.removeEventListener("abort", job.abort);
                    if (this.pending.get(job.text) === job) this.pending.delete(job.text);
                }
            }
        } finally { this.running = false; }
    }
}
