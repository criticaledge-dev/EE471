function invalidAudio() { return Object.assign(new Error("invalid WAV"), { outputCode: "audio" }); }

export async function readTtsResponse(response) {
    // Do not display raw response bodies: they may contain server diagnostics.
    if (!response.ok) throw Object.assign(new Error("HTTP failure"), { outputCode: "http", httpStatus: response.status });
    if (!response.headers.get("content-type")?.includes("audio/wav")) throw invalidAudio();
    const blob = await response.blob();
    if (blob.size <= 44 || blob.size > 2 * 1024 * 1024) throw invalidAudio();
    const buffer = await blob.arrayBuffer();
    const v = new DataView(buffer);
    const label = at => String.fromCharCode(...new Uint8Array(buffer, at, 4));
    if (label(0) !== "RIFF" || label(8) !== "WAVE" || v.getUint32(4, true) + 8 !== buffer.byteLength) throw invalidAudio();
    let fmt = false, data = false;
    for (let at = 12; at < buffer.byteLength;) {
        if (at + 8 > buffer.byteLength) throw invalidAudio();
        const kind = label(at), length = v.getUint32(at + 4, true), begin = at + 8;
        const end = begin + length + length % 2;
        if (end > buffer.byteLength) throw invalidAudio();
        if (kind === "fmt ") {
            if (fmt || length < 16 || v.getUint16(begin, true) !== 1 || v.getUint16(begin + 2, true) !== 1
                || v.getUint32(begin + 4, true) !== 16000 || v.getUint32(begin + 8, true) !== 32000
                || v.getUint16(begin + 12, true) !== 2 || v.getUint16(begin + 14, true) !== 16) throw invalidAudio();
            fmt = true;
        }
        if (kind === "data") { if (data || !fmt || !length || length % 2) throw invalidAudio(); data = true; }
        at = end;
    }
    if (!fmt || !data) throw invalidAudio();
    return blob;
}
