const digits = "zero one two three four five six seven eight nine".split(" ");
export const buttonWords = { ...Object.fromEntries(digits.map((word, i) => [String(i), word])),
    ".": "point", add: "plus", subtract: "minus", multiply: "times", divide: "over" };
const small = [...digits, "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"];
const tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"];

function integerWords(text) {
    text = text.replace(/^0+(?=\d)/, "");
    if (text.length > 15) return [...text].map(digit => digits[Number(digit)]).join(" ");
    const scales = ["", "thousand", "million", "billion", "trillion"];
    const groups = [];
    for (let end = text.length, group = 0; end > 0; end -= 3, group++) {
        let value = Number(text.slice(Math.max(0, end - 3), end));
        if (!value) continue;
        const words = [];
        if (value >= 100) { words.push(digits[Math.floor(value / 100)], "hundred"); value %= 100; }
        if (value >= 20) { words.push(tens[Math.floor(value / 10)]); value %= 10; }
        if (value) words.push(small[value]);
        if (scales[group]) words.push(scales[group]);
        groups.unshift(words.join(" "));
    }
    return groups.join(" ") || "zero";
}

export function resultWords(value) {
    const text = String(value);
    if (!/^-?\d+(?:\.\d+)?(?:e[+-]?\d+)?$/i.test(text) || !Number.isFinite(Number(text))) {
        throw new Error("Sonuç seslendirilebilir sonlu bir sayı değil.");
    }
    const [mantissa, exponent] = text.toLowerCase().split("e");
    const [whole, fraction] = mantissa.replace(/^-/, "").split(".");
    let words = (mantissa.startsWith("-") ? "minus " : "") + integerWords(whole);
    if (fraction) words += " point " + [...fraction].map(digit => digits[Number(digit)]).join(" ");
    if (exponent !== undefined) words += " times ten to the power of "
        + (exponent.startsWith("-") ? "minus " : "") + integerWords(exponent.replace(/^[+-]/, ""));
    return "is " + words;
}

// One producer/player at a time. Generation tickets invalidate all obsolete work.
export class SpeechQueue {
    constructor({ fetchAudio, createAudio, createURL, revokeURL, onError, onStatus = () => {}, onCancel = () => {},
        onMetrics = () => {}, now = () => performance.now(), maxItems = 12,
        setTimer = setTimeout, clearTimer = clearTimeout }) {
        Object.assign(this, { fetchAudio, createAudio, createURL, revokeURL, onError, onStatus, onCancel, onMetrics, maxItems });
        this.now = () => now();
        // Native Window timers reject a SpeechQueue receiver (Illegal invocation).
        // Invoke captured functions without turning them into queue methods.
        this.setTimer = (callback, delay) => setTimer(callback, delay);
        this.clearTimer = timer => clearTimer(timer);
        this.items = []; this.enabled = false; this.microphoneBusy = false; this.generation = 0;
        this.running = false; this.active = null;
    }
    ticket() { return this.generation; }
    readyStatus() { this.onStatus(!this.enabled ? "Sesli çıkış kapalı." : this.microphoneBusy
        ? "Mikrofon işlemi nedeniyle sesli çıkış bekletiliyor." : "Sesli çıkış açık; hesap makinesi tuşu bekleniyor."); }
    setEnabled(value) { this.enabled = value; if (!value) this.cancel(); else this.onError(""); this.readyStatus(); }
    setMicrophoneBusy(value) { this.microphoneBusy = value; if (value) this.cancel(); this.readyStatus(); }
    cancel() {
        this.generation++;
        this.items = [];
        this.onCancel();
        this.active?.controller?.abort();
        this.active?.finish?.();
        this.clean(this.active);
        this.onError("");
        this.onStatus("Önceki sesler iptal edildi.");
    }
    clean(item) {
        if (!item) return;
        if (item.audio) {
            item.audio.onended = item.audio.onerror = null;
            item.audio.pause(); item.audio.removeAttribute("src"); item.audio.load(); item.audio = null;
        }
        if (item.url) { this.revokeURL(item.url); item.url = null; }
    }
    key(key) { if (Object.hasOwn(buttonWords, key)) this.enqueue(buttonWords[key]); }
    result(value, ticket) {
        if (ticket !== this.generation || !this.enabled || this.microphoneBusy) return;
        try { this.enqueue(resultWords(value)); } catch { this.onError("Sonuç seslendirilemedi; hesaplama sonucu ekranda korunuyor."); }
    }
    enqueue(text) {
        if (!this.enabled || this.microphoneBusy) { this.readyStatus(); return; }
        if (this.items.length + (this.active ? 1 : 0) >= this.maxItems) {
            this.onError("Ses kuyruğu dolu; yeni ses atlandı. Hesap makinesini kullanabilirsiniz."); return;
        }
        this.items.push({ text, generation: this.generation, enqueuedAt: this.now() });
        if (!this.running) this.onStatus("Tuş sesi kuyruğa alındı.");
        void this.drain().catch(() => {
            this.onStatus("Ses kuyruğu beklenmedik biçimde durdu.");
            this.onError("Ses kuyruğu çalıştırılamadı; sesli çıkışı kapatıp tekrar açın. Hesap makinesini kullanabilirsiniz.");
        });
    }
    async drain() {
        if (this.running) return;
        this.running = true;
        try {
            while (this.items.length) {
                const item = this.items.shift();
                if (item.generation !== this.generation || !this.enabled || this.microphoneBusy) continue;
                this.active = item;
                let timer;
                let stage = "request";
                try {
                    item.controller = new AbortController();
                    timer = this.setTimer(() => item.controller.abort(), 20000);
                    this.onStatus("Flask /api/tts üzerinden ses isteniyor…");
                    const requestStarted = this.now();
                    const blob = await this.fetchAudio(item.text, item.controller.signal);
                    if (item.generation !== this.generation || !this.enabled || this.microphoneBusy) continue;
                    this.onMetrics({ requestWaitMs: Math.max(0, this.now() - requestStarted),
                        playbackQueueMs: Math.max(0, requestStarted - item.enqueuedAt) });
                    if (timer !== undefined) this.clearTimer(timer);
                    this.onStatus(`WAV yanıtı doğrulandı (${blob.size ?? "?"} bayt); tarayıcı oynatması başlatılıyor…`);
                    stage = "playback";
                    item.url = this.createURL(blob);
                    item.audio = this.createAudio(item.url);
                    await new Promise((resolve, reject) => {
                        item.finish = resolve;
                        item.audio.onended = () => { item.ended = true; resolve(); };
                        item.audio.onerror = () => reject(new Error("media-error"));
                        timer = this.setTimer(() => reject(new Error("playback-timeout")), 30000);
                        Promise.resolve(item.audio.play()).then(() => {
                            if (!item.ended && item.generation === this.generation) this.onStatus("Tarayıcı ses oynatmasını başlattı.");
                        }).catch(reject);
                    });
                    if (item.generation === this.generation) this.onStatus("Tarayıcı ses oynatmasını tamamladı.");
                } catch (error) {
                    if (item.generation === this.generation && this.enabled && !this.microphoneBusy) {
                        let message = stage === "request" ? "Ses isteği tamamlanamadı; Flask bağlantısını kontrol edin."
                            : "Tarayıcı WAV sesini oynatamadı; ses aygıtını ve dosya desteğini kontrol edin.";
                        if (error.outputCode === "http") message = `Flask TTS isteği HTTP ${error.httpStatus} döndürdü. `
                            + (error.httpStatus === 503 ? "Sunucunun Speech yapılandırması eksik." : "Sunucuda ses üretimi tamamlanamadı.");
                        else if (error.outputCode === "audio") message = "Flask yanıtı boş veya geçerli PCM WAV içermiyor; oynatma başlatılmadı.";
                        else if (stage === "request" && error.name === "AbortError") message = "Flask TTS yanıtı 20 saniyede alınamadı; ses isteği iptal edildi.";
                        else if (stage === "playback" && error.name === "NotAllowedError") message = "Tarayıcı audio.play() çağrısını NotAllowedError ile reddetti. Site ses/oynatma izinlerini kontrol edin.";
                        else if (stage === "playback" && error.name === "NotSupportedError") message = "Tarayıcı audio.play() çağrısını NotSupportedError ile reddetti; WAV çözümlenemedi.";
                        else if (stage === "playback" && error.message === "playback-timeout") message = "Tarayıcı ses oynatmasını 30 saniyede tamamlamadı.";
                        this.onStatus("Sesli çıkış hatası.");
                        this.onError(message + " Bu sırada hesaplama sonucu korunuyor.");
                    }
                } finally {
                    this.clearTimer(timer);
                    this.clean(item);
                    this.active = null;
                }
            }
        } finally { this.running = false; }
    }
}
