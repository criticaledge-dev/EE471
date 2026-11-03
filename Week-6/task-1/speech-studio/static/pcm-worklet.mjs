import { StreamingPcm16, pcmLittleEndian } from "./pcm-resampler.mjs";

class LivePcmProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.resampler = new StreamingPcm16(sampleRate);
    this.packet = new Int16Array(1600); // 100 ms, bounded
    this.used = this.sentSamples = this.credits = 0;
    this.active = this.ending = this.finished = false;
    this.port.onmessage = ({ data }) => {
      if (data.type === "start" && !this.ending) {
        this.credits = 4;
        this.active = true;
      } else if (data.type === "credit") {
        this.credits = Math.min(4, this.credits + 1);
        if (this.ending) this.flush();
      } else if (data.type === "flush") {
        this.active = false;
        this.ending = true;
        this.flush();
      }
    };
  }

  fail() {
    if (!this.finished) this.port.postMessage({ type: "error", error: "Ses akışı yetişemedi; tampon sınırına ulaşıldı." });
    this.active = false;
    this.finished = true;
  }

  emit() {
    if (!this.used) return true;
    if (!this.credits) return false;
    const pcm = pcmLittleEndian(this.packet.subarray(0, this.used));
    this.port.postMessage({ type: "pcm", pcm }, [pcm]);
    this.credits--;
    this.sentSamples += this.used;
    this.used = 0;
    return true;
  }

  flush() {
    if (this.finished || !this.emit()) return;
    this.finished = true;
    this.port.postMessage({ type: "flushed" }); // ordered after all final PCM messages
  }

  process(inputs, outputs) {
    // The graph remains active via a silent output. Never monitor microphone audio.
    for (const output of outputs) for (const channel of output) channel.fill(0);
    if (this.active && !this.finished) {
      for (const sample of this.resampler.push(inputs[0] || [])) {
        if (this.sentSamples + this.used >= 960000) {
          this.active = false;
          this.ending = true;
          this.flush();
          break;
        }
        this.packet[this.used++] = sample;
        if (this.used === this.packet.length && !this.emit()) {
          this.fail();
          break;
        }
      }
    }
    return !this.finished;
  }
}

registerProcessor("live-pcm", LivePcmProcessor);
