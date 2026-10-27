import { StreamingPcm16, pcmLittleEndian } from "./pcm-resampler.mjs";

class VoiceCapture extends AudioWorkletProcessor {
    constructor() {
        super();
        this.converter = new StreamingPcm16(sampleRate);
        this.active = false;
        this.count = 0;
        this.packet = [];
        this.port.onmessage = ({ data }) => {
            if (data === "start") this.active = true;
            if (data === "flush") this.finish();
        };
    }
    send() {
        if (!this.packet.length) return;
        const buffer = pcmLittleEndian(Int16Array.from(this.packet));
        this.packet = [];
        this.port.postMessage({ type: "pcm", buffer }, [buffer]);
    }
    finish() {
        if (!this.active) return;
        this.active = false;
        this.send();
        this.port.postMessage({ type: "flushed" });
    }
    process(inputs, outputs) {
        for (const output of outputs) for (const channel of output) channel.fill(0);
        if (this.active && inputs[0]?.length) {
            for (const sample of this.converter.push(inputs[0])) {
                if (this.count >= 240000) break;
                this.packet.push(sample);
                this.count++;
                if (this.packet.length === 1600) this.send();
            }
            if (this.count >= 240000) this.finish();
        }
        return true;
    }
}
registerProcessor("voice-capture", VoiceCapture);
