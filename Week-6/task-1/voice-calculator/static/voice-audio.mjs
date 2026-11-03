export function makeWav(chunks) {
    const size = chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
    if (!size || size % 2 || size > 15 * 16000 * 2) throw new Error("Kayıt boş veya 15 saniye sınırını aşıyor.");
    const wav = new ArrayBuffer(44 + size);
    const view = new DataView(wav);
    function label(offset, text) { [...text].forEach((char, i) => view.setUint8(offset + i, char.charCodeAt(0))); }
    label(0, "RIFF"); view.setUint32(4, 36 + size, true); label(8, "WAVE");
    label(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, 1, true); view.setUint32(24, 16000, true);
    view.setUint32(28, 32000, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    label(36, "data"); view.setUint32(40, size, true);
    let offset = 44;
    for (const chunk of chunks) { new Uint8Array(wav, offset, chunk.byteLength).set(new Uint8Array(chunk)); offset += chunk.byteLength; }
    return wav;
}
