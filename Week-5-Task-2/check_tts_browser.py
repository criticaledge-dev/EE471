r"""Headless Chrome regression: real page/native timers/HTTP; mocked Azure and media.

Run from Task 2 with: .venv\Scripts\python.exe check_tts_browser.py
Never loads .env, calls Azure, or requests a physical microphone/audio device.
"""
import io
import json
from pathlib import Path
import re
import subprocess
from threading import Thread
from unittest.mock import patch
import wave

from werkzeug.serving import WSGIRequestHandler, make_server
import app as application

PROBE = r"""
<script>
const checks = {plays: 0, phases: [], errors: []};
function report(ok, error) {
  const pre = document.createElement('pre'); pre.id = 'browser-check-result';
  pre.textContent = JSON.stringify({ok, ...checks, error}); document.body.append(pre);
}
window.addEventListener('error', e => checks.errors.push(e.error?.name || 'script-error'));
window.addEventListener('unhandledrejection', e => checks.errors.push(e.reason?.name || 'promise-error'));
window.Audio = class {
  play() { checks.plays++; setTimeout(() => this.onended?.(), 5); return Promise.resolve(); }
  pause() {} removeAttribute() {} load() {}
};
Object.defineProperty(navigator, 'mediaDevices', {configurable: true, value: {
  async getUserMedia() { return {getTracks: () => [{onended: null, stop() {}}]}; }
}});
window.AudioContext = class {
  constructor() { this.state = 'running'; this.destination = {}; this.audioWorklet = {async addModule() {}}; }
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
async function waitFor(predicate) {
  for (let i = 0; i < 500; i++) { if (predicate()) return; await new Promise(r => setTimeout(r, 10)); }
  throw new Error('check-timeout');
}
(async () => {
  try {
    await waitFor(() => window.calculatorAudio && window.calculatorVoice);
    const toggle = document.querySelector('#tts-enabled');
    const five = document.querySelector('[data-digit="5"]');
    function enabled(value) { toggle.checked = value; toggle.dispatchEvent(new Event('change')); }
    async function pressAndVerify(count, phase) {
      five.click();
      await waitFor(() => checks.plays === count && !window.calculatorAudio.running);
      checks.phases.push(phase);
    }
    enabled(true); await pressAndVerify(1, 'enabled-physical-five');
    enabled(false); enabled(true); await pressAndVerify(2, 'off-on-physical-five');
    document.querySelector('#voice-start').click();
    await waitFor(() => document.querySelector('#voice-status').textContent.includes('Dinleniyor'));
    if (!window.calculatorAudio.microphoneBusy) throw new Error('microphone-guard-missing');
    document.querySelector('#voice-stop').click();
    await waitFor(() => !document.querySelector('#voice-start').disabled);
    if (document.querySelector('#voice-command').textContent !== '5 + 2 = 7') throw new Error('voice-input-regression');
    if (checks.plays !== 2) throw new Error('programmatic-voice-spoke');
    await pressAndVerify(3, 'microphone-start-stop-physical-five');
    checks.cacheMetricsVisible = document.querySelector('#tts-metrics').textContent.includes('HTTP: 1;')
      && document.querySelector('#tts-metrics').textContent.includes('önbellek: 2;');
    if (!checks.cacheMetricsVisible) throw new Error('cache-metrics-missing');
    if (checks.errors.length) throw new Error('browser-javascript-error');
    enabled(false); report(true);
  } catch (error) { report(false, error.message); }
})();
</script>
"""


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


def main():
    browser = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if not browser.is_file():
        raise SystemExit("Chrome bulunamadı; bu tarayıcı kontrolü çalıştırılamadı.")
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\0" * 320)
    tts_requests = []

    def tts(text):
        tts_requests.append(text)
        return output.getvalue()

    original_view = application.app.view_functions["index"]
    application.app.view_functions["index"] = lambda: original_view() + PROBE
    server = make_server("127.0.0.1", 0, application.app, threaded=True, request_handler=QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    profile = Path(__file__).resolve().parent / "tmp" / "tts-browser-regression-profile"
    try:
        # These replace speech entry points before the real Flask app is served.
        with patch.object(application, "synthesize_speech", side_effect=tts), \
             patch.object(application, "transcribe_pcm", return_value="five plus two is"):
            thread.start()
            result = subprocess.run([
                str(browser), "--headless", "--disable-gpu", "--disable-background-networking",
                "--disable-extensions", "--no-first-run", "--no-default-browser-check", "--log-level=3",
                "--autoplay-policy=no-user-gesture-required", "--user-data-dir=" + str(profile),
                "--virtual-time-budget=10000", "--dump-dom", f"http://127.0.0.1:{server.server_port}/",
            ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            match = re.search(r'<pre id="browser-check-result">(.*?)</pre>', result.stdout, re.S)
            if not match:
                raise SystemExit("Tarayıcı kontrolü sonuç üretemedi; gerçek ses doğrulanmadı.")
            report = json.loads(match.group(1))
            report["tts_http_requests"] = len(tts_requests)
            assert report["ok"] and len(tts_requests) == 1, report
            print(json.dumps(report, ensure_ascii=True))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        application.app.view_functions["index"] = original_view


if __name__ == "__main__":
    main()
