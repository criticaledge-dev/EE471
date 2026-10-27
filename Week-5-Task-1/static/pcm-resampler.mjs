// Stateful area-weighted resampling: phase and partial integrals span blocks.
export class StreamingPcm16 {
  constructor(inputRate, outputRate = 16000) {
    if (!Number.isFinite(inputRate) || inputRate < 8000 || inputRate > 192000) {
      throw new Error("Unsupported AudioContext sample rate");
    }
    this.step = inputRate / outputRate;
    this.fill = 0;
    this.sum = 0;
    this.samples = 0;
  }

  push(channels) {
    if (!channels.length) return new Int16Array(0);
    const output = [];
    for (let i = 0; i < channels[0].length; i++) {
      let value = 0;
      for (const channel of channels) value += Number.isFinite(channel[i]) ? channel[i] : 0;
      value /= channels.length;
      let remaining = 1;
      while (remaining > 1e-10) {
        const weight = Math.min(remaining, this.step - this.fill);
        this.sum += value * weight;
        this.fill += weight;
        remaining -= weight;
        if (this.fill + 1e-10 >= this.step) {
          const sample = Math.max(-1, Math.min(1, this.sum / this.step));
          output.push(Math.round(sample * (sample < 0 ? 32768 : 32767)));
          this.fill = this.sum = 0;
          this.samples++;
        }
      }
    }
    return Int16Array.from(output);
  }
}

export function pcmLittleEndian(samples) {
  const buffer = new ArrayBuffer(samples.length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < samples.length; i++) view.setInt16(i * 2, samples[i], true);
  return buffer;
}
