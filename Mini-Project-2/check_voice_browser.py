r"""Headless real page/Flask/Library test with mocked microphone and STT.
No hardware, Azure or real .env access. Run: .venvScriptspython.exe check_voice_browser.py
"""
import json
from pathlib import Path
import re
import subprocess
from threading import Thread
from unittest.mock import patch

from werkzeug.serving import make_server
import app as library_app
from custom_classes import Book, DVD, LibraryCollection
from check_commands_browser import QuietHandler

TRANSCRIPTS = [
    "Create item type book title The Hobbit author Tolkien pages 310",
    "Get item four", "List available books",
    "Replace item four, title Test Book, author Test Author, pages 230",
    "Update item four pages three hundred twenty", "Check out item four",
    "Return item four", "Delete item four", "Update item two title The author of books",
]
PROBE = r"""
<script>
const voiceCheck = {steps: [], errors: [], stoppedTracks: 0};
window.addEventListener('error', e => voiceCheck.errors.push(e.error?.name || 'script-error'));
window.addEventListener('unhandledrejection', e => voiceCheck.errors.push(e.reason?.name || 'promise-error'));
Object.defineProperty(navigator, 'mediaDevices', {configurable: true, value: {
  async getUserMedia() {
    const track = {onended: null, stop() { voiceCheck.stoppedTracks++; }};
    return {getTracks: () => [track]};
  }
}});
window.AudioContext = class {
  constructor() { this.sampleRate = 48000; this.state = 'running'; this.destination = {}; this.audioWorklet = {async addModule() {}}; }
  createMediaStreamSource() { return {connect() {}, disconnect() {}}; }
  async resume() {} async close() { this.state = 'closed'; }
};
window.AudioWorkletNode = class {
  constructor() { this.port = {close() {}, postMessage: data => {
    if (data === 'flush') queueMicrotask(() => {
      this.port.onmessage?.({data: {type: 'pcm', buffer: new ArrayBuffer(320)}});
      this.port.onmessage?.({data: {type: 'flushed'}});
    });
  }}; }
  connect() {} disconnect() {}
};
const el = id => document.getElementById(id);
function assertVoice(value, label) { if (!value) throw new Error(label); }
async function waitVoice(predicate) {
  for (let i=0;i<500;i++) { if (predicate()) return; await new Promise(r=>setTimeout(r,10)); }
  throw new Error('voice-check-timeout');
}
async function recordOne(expected, parserError=false) {
  el('voice-start').click();
  await waitVoice(()=>!el('voice-stop').disabled);
  assertVoice(el('command-run').disabled && el('save').disabled,'voice-not-exclusive');
  el('voice-stop').click();
  await waitVoice(()=>!el('voice-start').disabled);
  assertVoice(el(parserError?'command-error':'command-result').textContent.includes(expected),'unexpected-result');
  voiceCheck.steps.push(parserError?'parser-needs-manual-correction':el('voice-transcript').textContent.split(' ')[0].toLowerCase());
}
(async()=>{
  try {
    await waitVoice(()=>el('command-form').getAttribute('aria-busy')==='false');
    await recordOne('ID 4');
    await recordOne('Pages: 310');
    await recordOne('4:');
    await recordOne('Successfully replaced');
    await recordOne('Successfully updated');
    await recordOne('has been checked out');
    await recordOne('Successful return');
    await recordOne('Successfully deleted item 4');
    await recordOne('Ambiguous',true);
    assertVoice(el('command-text').value==='Update item two title The author of books','transcript-not-preserved');
    assertVoice(el('voice-status').textContent.includes('manual correction'),'manual-step-misreported');
    el('command-text').value='Update item two, title The author of books';
    el('command-form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
    await waitVoice(()=>!el('command-run').disabled);
    assertVoice(el('command-result').textContent.includes('Successfully updated item 2'),'manual-correction-failed');
    assertVoice(el('voice-status').textContent.includes('manual correction'),'manual-correction-called-voice-success');
    el('voice-start').click(); await waitVoice(()=>!el('voice-stop').disabled);
    el('voice-cancel').click(); await waitVoice(()=>!el('voice-start').disabled);
    assertVoice(el('voice-status').textContent.includes('canceled'),'cancel-failed');
    assertVoice(voiceCheck.errors.length===0,'javascript-errors');
    const pre=document.createElement('pre');pre.id='voice-check-result';
    pre.textContent=JSON.stringify({ok:true,...voiceCheck});document.body.append(pre);
  } catch(error) {
    const pre=document.createElement('pre');pre.id='voice-check-result';
    pre.textContent=JSON.stringify({ok:false,...voiceCheck,failure:error.message});document.body.append(pre);
  }
})();
</script>
"""


def main():
    browser = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if not browser.is_file():
        raise SystemExit("Chrome not found; headless voice check was not run.")
    collection = LibraryCollection()
    collection.add_item(Book("The Hobbit", "Tolkien", 310))
    collection.add_item(DVD("Inception", "Christopher Nolan", 148))
    collection.add_item(Book("1984", "Orwell", 328))
    original = library_app.app.view_functions["index"]
    library_app.app.view_functions["index"] = lambda: original() + PROBE
    server = make_server("127.0.0.1", 0, library_app.app, threaded=True, request_handler=QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    pending = list(TRANSCRIPTS)
    try:
        with patch.object(library_app, "collection", collection), \
             patch.object(library_app, "transcribe_pcm", side_effect=lambda *_: pending.pop(0)) as stt:
            thread.start()
            profile = Path(__file__).resolve().parent / "tmp" / "voice-browser-profile"
            result = subprocess.run([
                str(browser), "--headless", "--disable-gpu", "--disable-background-networking", "--disable-extensions",
                "--no-first-run", "--no-default-browser-check", "--log-level=3", "--user-data-dir=" + str(profile),
                "--virtual-time-budget=20000", "--dump-dom", f"http://127.0.0.1:{server.server_port}/",
            ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=40)
            match = re.search(r'<pre id="voice-check-result">(.*?)</pre>', result.stdout, re.S)
            if not match:
                raise SystemExit("No browser voice result; real hardware remains unverified.")
            report = json.loads(match.group(1))
            report["mock_stt_calls"] = stt.call_count
            assert report["ok"] and not pending and stt.call_count == 9, report
            assert collection.get_item(2).title == "The author of books"
            assert len(collection.list_items()) == 3
            print(json.dumps(report))
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        library_app.app.view_functions["index"] = original


if __name__ == "__main__":
    main()
