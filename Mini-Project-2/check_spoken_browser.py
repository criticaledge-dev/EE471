"""Real Flask/page/event wiring, mocked Azure + microphone + Audio. No actual sound."""
import json
from pathlib import Path
import re
import subprocess
from threading import Thread
from unittest.mock import patch

from werkzeug.serving import make_server
import app as library_app
from custom_classes import Book, DVD, LibraryCollection
from speech_service import NoSpeechError
from test_voice import wav
from check_commands_browser import QuietHandler
from check_voice_browser import PROBE as VOICE_PROBE

# The prefix replaces all hardware boundaries before the real page modules execute.
PROBE = VOICE_PROBE.split('const el = id')[0] + r"""
const spokenCheck = {steps: [], texts: [], plays: 0, pauses: 0, revoked: 0, writes: []};
let rejectPlay = false, holdPlay = false, holdSpeech = false, releaseSpeech, failSpeech = false;
let holdWrite = false, releaseWrite, failNextList = false;
window.Audio = class {
  constructor(url) { this.src = url; }
  play() {
    spokenCheck.plays++;
    if (rejectPlay) return Promise.reject(new DOMException('Mock autoplay denial', 'NotAllowedError'));
    if (!holdPlay) queueMicrotask(() => this.onended?.());
    return Promise.resolve();
  }
  pause() { spokenCheck.pauses++; }
  removeAttribute() { this.src = ''; } load() {}
};
const revoke = URL.revokeObjectURL.bind(URL);
URL.revokeObjectURL = url => { spokenCheck.revoked++; revoke(url); };
const nativeFetch = window.fetch.bind(window);
window.fetch = async (url, options = {}) => {
  if (url === '/api/tts') {
    spokenCheck.texts.push(JSON.parse(options.body).text);
    if (failSpeech) { failSpeech = false; return new Response('{}', {status:502}); }
    const response = await nativeFetch(url, options);
    if (holdSpeech) await new Promise(resolve => { releaseSpeech = resolve; });
    return response;
  }
  if (['POST','PUT','PATCH','DELETE'].includes(options.method) && url !== '/api/voice-input') {
    spokenCheck.writes.push({url, method: options.method});
    if (holdWrite) await new Promise(resolve => { releaseWrite = resolve; });
  }
  if (failNextList && (!options.method || options.method === 'GET') && /^\/api\/items(?:\?|$)/.test(url)) {
    failNextList = false; throw new Error('Mock refresh network failure');
  }
  return nativeFetch(url, options);
};
const el = id => document.getElementById(id);
const assert = (value, label) => { if (!value) throw new Error(label); };
async function wait(predicate) {
  for (let i=0;i<700;i++) { if (predicate()) return; await new Promise(r=>setTimeout(r,10)); }
  throw new Error('spoken-check-timeout-' + spokenCheck.steps.at(-1));
}
function submit(text) {
  el('command-text').value=text;
  el('command-form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
}
async function command(text, match, error=false, speak=true) {
  const before=spokenCheck.texts.length;
  submit(text);
  await wait(()=>!el('command-run').disabled && !el(error?'command-error':'command-result').hidden);
  assert(el(error?'command-error':'command-result').textContent.includes(match),'wrong-command-result');
  if (speak) {
    await wait(()=>spokenCheck.texts.length===before+1);
    assert(spokenCheck.texts[before].includes(match),'wrong-spoken-result');
    await wait(()=>el('spoken-status').textContent.includes('completed') || !el('spoken-error').hidden);
  } else assert(spokenCheck.texts.length===before,'unexpected-speech');
  spokenCheck.steps.push(text.split(' ')[0]);
}
(async()=>{
 try {
  await wait(()=>el('command-form').getAttribute('aria-busy')==='false');
  assert(!el('spoken-enabled').checked && spokenCheck.texts.length===0,'not-silent-default');
  await command('Get item 1','Item 1',false,false);
  assert(el('spoken-text').textContent.includes('Item 1'),'last-text-missing-when-off');
  el('spoken-enabled').checked=true; el('spoken-enabled').dispatchEvent(new Event('change'));
  holdWrite=true;
  submit('Create item; type: book; title: Test Book; author: Test Author; pages: three hundred and ten.');
  await wait(()=>Boolean(releaseWrite));
  assert(spokenCheck.texts.length===0,'success-speech-before-api');
  assert(!el('spoken-enabled').disabled && !el('spoken-stop').disabled,'speech-controls-blocked');
  holdWrite=false; releaseWrite();
  await wait(()=>!el('command-run').disabled && el('spoken-status').textContent.includes('completed'));
  assert(spokenCheck.texts[0].includes("created book 'Test Book' with ID 4"),'create-speech');
  spokenCheck.steps.push('create-after-api');
  await command('Get item 4','Item 4');
  await command('List available books','items found');
  await command('Replace item 4, title Revised, author Tolkien, pages 320','replaced item 4');
  await command('Update item 4 pages 330','updated item 4');
  await command('Check out item 4','has been checked out');
  await command('Check out item 4','HTTP 409',true);
  await command('Return item 4','Successful return');
  await command('Check out item 2','Do not scratch the disc.');
  failNextList=true;
  await command('Delete item 4','deleted item 4');
  assert(spokenCheck.texts.at(-1).includes('operation succeeded, but the list could not be refreshed'),'warning-missing');
  const writeCount=spokenCheck.writes.length;
  await command('Delete item 4','deleted item 4',false,false);
  assert(spokenCheck.writes.length===writeCount,'mutation-repeated');
  await command('Get item 999','999 was not found',true);
  await command('Unknown command','Unknown command',true);
  await command('List checked out books','No items match');
  rejectPlay=true;
  await command('Get item 1','Item 1');
  assert(!el('spoken-error').hidden && !el('command-result').hidden,'play-rejection-hidden');
  const writesBeforeReplay=spokenCheck.writes.length;
  rejectPlay=false; el('spoken-play').click();
  await wait(()=>el('spoken-status').textContent.includes('completed'));
  assert(spokenCheck.writes.length===writesBeforeReplay,'replay-mutated'); spokenCheck.steps.push('play-retry');
  failSpeech=true;
  await command('Return item 2','Successful return');
  assert(!el('spoken-error').hidden && el('command-error').hidden,'tts-damaged-library-success');
  holdSpeech=true;
  submit('Get item 1'); await wait(()=>Boolean(releaseSpeech));
  const playsBeforeOff=spokenCheck.plays;
  el('spoken-enabled').checked=false; el('spoken-enabled').dispatchEvent(new Event('change'));
  holdSpeech=false; releaseSpeech(); await new Promise(r=>setTimeout(r,30));
  assert(spokenCheck.plays===playsBeforeOff,'late-speech-played');
  el('spoken-enabled').checked=true; el('spoken-enabled').dispatchEvent(new Event('change'));
  holdPlay=true;
  submit('Get item 1'); await wait(()=>el('spoken-status').textContent.includes('Playing'));
  const pausesBeforeMic=spokenCheck.pauses;
  el('voice-start').click(); await wait(()=>!el('voice-stop').disabled);
  assert(spokenCheck.pauses>pausesBeforeMic && el('spoken-play').disabled,'microphone-not-exclusive');
  const beforeVoice=spokenCheck.texts.length;
  holdPlay=false; el('voice-stop').click();
  await wait(()=>!el('voice-start').disabled && spokenCheck.texts.length===beforeVoice+1 && el('spoken-status').textContent.includes('completed'));
  assert(voiceCheck.stoppedTracks===1,'microphone-track-not-cleaned'); spokenCheck.steps.push('voice-result');
  el('voice-start').click(); await wait(()=>!el('voice-stop').disabled); el('voice-stop').click();
  await wait(()=>!el('voice-error').hidden && el('spoken-status').textContent.includes('completed'));
  assert(spokenCheck.texts.at(-1).includes('No complete speech'),'stt-failure-not-spoken');
  spokenCheck.steps.push('stt-silence');
  window.dispatchEvent(new Event('pagehide'));
  assert(!el('spoken-enabled').checked,'pagehide-did-not-disable');
  assert(voiceCheck.errors.length===0,'javascript-errors');
  const pre=document.createElement('pre'); pre.id='spoken-check-result';
  pre.textContent=JSON.stringify({ok:true,...spokenCheck,errors:voiceCheck.errors,stoppedTracks:voiceCheck.stoppedTracks}); document.body.append(pre);
 } catch(error) {
  const pre=document.createElement('pre'); pre.id='spoken-check-result';
  pre.textContent=JSON.stringify({ok:false,...spokenCheck,errors:voiceCheck.errors,failure:error.message}); document.body.append(pre);
 }
})();
</script>
"""


def main():
    browser = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    if not browser.is_file():
        raise SystemExit('Chrome not found; spoken browser check was not run.')
    collection = LibraryCollection()
    collection.add_item(Book('The Hobbit', 'Tolkien', 310))
    collection.add_item(DVD('Inception', 'Christopher Nolan', 148))
    collection.add_item(Book('1984', 'Orwell', 328))
    original = library_app.app.view_functions['index']
    library_app.app.view_functions['index'] = lambda: original() + PROBE
    server = make_server('127.0.0.1', 0, library_app.app, threaded=True, request_handler=QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    try:
        with patch.object(library_app, 'collection', collection), \
             patch.object(library_app, 'synthesize_speech', return_value=wav()) as tts, \
             patch.object(library_app, 'transcribe_pcm', side_effect=['List items', NoSpeechError()]) as stt, \
             patch('speech_service.load_dotenv', side_effect=AssertionError('dotenv forbidden')):
            thread.start()
            profile = Path(__file__).resolve().parent / 'tmp' / 'spoken-browser-profile'
            result = subprocess.run([str(browser), '--headless', '--mute-audio', '--disable-gpu', '--disable-background-networking',
                '--disable-extensions', '--no-first-run', '--no-default-browser-check', '--log-level=3',
                '--user-data-dir=' + str(profile), '--virtual-time-budget=30000', '--dump-dom',
                f'http://127.0.0.1:{server.server_port}/'], capture_output=True, text=True,
                encoding='utf-8', errors='replace', timeout=50)
            match = re.search(r'<pre id="spoken-check-result">(.*?)</pre>', result.stdout, re.S)
            if not match:
                raise SystemExit('No spoken browser result; real media behavior remains unverified.')
            report = json.loads(match.group(1))
            assert report['ok'], report
            # Report counts, never keys, audio, or production/user transcripts.
            print(json.dumps({'ok': True, 'steps': report['steps'], 'mockTtsCalls': tts.call_count,
                'mockSttCalls': stt.call_count, 'mockPlayCalls': report['plays'],
                'revokedURLs': report['revoked'], 'stoppedMockTracks': report['stoppedTracks'], 'errors': report['errors']}))
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        library_app.app.view_functions['index'] = original


if __name__ == '__main__':
    main()
