"""Real isolated Flask/Chrome PUT/PATCH check; no .env, microphone, Azure or sound."""
import json
from pathlib import Path
import re
import subprocess
from threading import Thread
from unittest.mock import patch

from werkzeug.serving import make_server
import app as library_app
from custom_classes import Book, LibraryCollection
from check_commands_browser import QuietHandler

PROBE = r"""
<script type="module">
const requests = [], steps = [], errors = [];
const commandCases = __COMMAND_CASES__;
let failListOnce = false;
const nativeFetch = window.fetch.bind(window);
window.fetch = (url, options = {}) => {
  if (String(url).includes('/api/tts') || String(url).includes('/api/voice-input')) throw new Error('speech-forbidden');
  requests.push({url: String(url), method: options.method || 'GET', body: options.body ? JSON.parse(options.body) : null});
  if (failListOnce && (!options.method || options.method === 'GET') && /^\/api\/items(?:\?|$)/.test(String(url))) {
    failListOnce = false; return Promise.reject(new Error('mock-list-refresh-failure'));
  }
  return nativeFetch(url, options);
};
window.addEventListener('error', e => errors.push(e.error?.name || 'script-error'));
window.addEventListener('unhandledrejection', e => errors.push(e.reason?.name || 'promise-error'));
const el = id => document.getElementById(id);
function check(value, label) { if (!value) throw new Error(label); }
async function wait(predicate) {
  for (let i=0;i<600;i++) {if (predicate()) return; await new Promise(resolve => setTimeout(resolve,10));}
  throw new Error('put-browser-timeout');
}
const standard = {title:'revised Hobbit', author:'Tolkien', page_count:200};
(async () => {
 try {
  await wait(() => el('command-form').getAttribute('aria-busy') === 'false');
  const fixture = await (await nativeFetch('/api/items/6')).json();
  check(fixture.id === 6 && fixture.type === 'book' && fixture.title === 'PUT fixture', 'wrong-seeded-fixture');
  const fixtureThree = await (await nativeFetch('/api/items/3')).json();
  check(fixtureThree.id === 3 && fixtureThree.type === 'book', 'wrong-book-three-fixture');
  const cases = [
   ...commandCases.map(c => ({text:c.text, method:c.method, body:c.fields, item_id:c.item_id, name:c.case})),
   {text:'Replace item six. Title revised Hobbit. Author Tolkien, pages 200.', method:'PUT', body:standard},
   {text:'Replace item 6. Title revised Hobbit. Author Tolkien, pages 200.', method:'PUT', body:standard},
   {text:'Replace item 6, title revised Hobbit, author Tolkien, pages 200', method:'PUT', body:standard},
   {text:'Replace item 6 title revised Hobbit author Tolkien pages 200', method:'PUT', body:standard},
   {text:'Update item six. Title revised Hobbit. Author Tolkien, pages 200.', method:'PATCH', body:standard},
   {text:'Replace item six. Title "revised Hobbit. Author notes". Author "J.D. Salinger.", pages 200.',
    method:'PUT', body:{title:'revised Hobbit. Author notes',author:'J.D. Salinger.',page_count:200}},
  ];
  for (const example of cases) {
   const itemId = example.item_id || 6, path = '/api/items/' + itemId;
   const before = requests.length;
   el('command-text').value=example.text;
   el('command-form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
   await wait(() => !el('command-run').disabled && !el('command-result').hidden);
   const sent = requests.slice(before), writes = sent.filter(r => r.method !== 'GET');
   check(sent[0].method === 'GET' && sent[0].url === path,'missing-fresh-type-get');
   check(sent[1].method === example.method && sent[1].url === path,'wrong-write-order');
   check(writes.length === 1,'duplicate-mutation');
   check(Object.keys(writes[0].body).length === Object.keys(example.body).length,'unexpected-write-fields');
   const saved = await (await nativeFetch(path)).json();
   for (const [key,value] of Object.entries(example.body)) {
    check(writes[0].body[key] === value,'wrong-body-'+key);
    check(saved[key] === value,'wrong-saved-'+key);
   }
   check(saved.id === itemId && saved.type === 'book' && saved.is_available === true,'immutable-fields-changed');
   steps.push(example.name || example.method);
  }
  const refreshText = 'Replace item 3 title "Refresh success" author Tolkien, pages 201';
  const beforeRefresh = requests.length;
  failListOnce = true; el('command-text').value = refreshText;
  el('command-form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
  await wait(() => !el('command-run').disabled && !el('command-result').hidden && !el('command-warning').hidden);
  const refreshWrites = requests.slice(beforeRefresh).filter(r => r.method !== 'GET');
  check(refreshWrites.length === 1 && refreshWrites[0].method === 'PUT','refresh-repeated-mutation');
  const savedAfterRefresh = await (await nativeFetch('/api/items/3')).json();
  check(savedAfterRefresh.title === 'Refresh success' && savedAfterRefresh.page_count === 201,'write-not-preserved-after-refresh-error');
  steps.push('refresh-failure-after-success');
  const retryStart = requests.length;
  el('command-form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
  await wait(() => !el('command-run').disabled && el('command-warning').hidden);
  check(requests.length === retryStart + 1 && requests.at(-1).method === 'GET' && requests.at(-1).url === '/api/items','refresh-retry-not-get-only');
  steps.push('refresh-only-GET');
  for (const text of ['Replace item six. Title revised Hobbit. Author Tolkien',
   'Replace item six. Title revised Hobbit, pages 200',
   'Replace item six. Title revised Hobbit. Author Tolkien, pages -200',
   'Update item six pages 200 title The author of books',
   'Replace item 3 title. X titled. Y author. Tolkien, pages 200',
   '\u201cUpdate item 3 pages 330.']) {
   const before=requests.length;
   el('command-text').value=text;
   el('command-form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
   await wait(() => !el('command-run').disabled && !el('command-error').hidden);
   check(requests.length === before,'invalid-command-reached-api'); steps.push('expected-error');
  }
  check(errors.length === 0,'javascript-errors');
  const result=document.createElement('pre'); result.id='put-browser-result';
  result.textContent=JSON.stringify({ok:true,steps,errors,fixtureIds:[3,6],
   putCases:cases.filter(c=>c.method==='PUT').length,patchCases:cases.filter(c=>c.method==='PATCH').length,
   invalidCases:6,refreshMutationCases:1,refreshRetries:1}); document.body.append(result);
 } catch(error) {
  const result=document.createElement('pre'); result.id='put-browser-result';
  result.textContent=JSON.stringify({ok:false,steps,errors,failure:error.message}); document.body.append(result);
 }
})();
</script>
"""


def main():
    browser = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    if not browser.is_file():
        raise SystemExit('Chrome not found; PUT browser check was not run.')
    # Test setup allocates ID 6 through the real model; production seeds stay untouched.
    collection = LibraryCollection()
    for number in range(1, 6):
        collection.add_item(Book(f'Test fixture {number}', 'Test author', 10))
    assert collection.add_item(Book('PUT fixture', 'Fixture author', 310)) == 6
    assert collection.get_item(3).to_dict()['type'] == 'book'
    command_cases = json.loads((Path(__file__).resolve().parent / 'command-regression-cases.json').read_text(encoding='utf-8'))
    probe = PROBE.replace('__COMMAND_CASES__', json.dumps(command_cases))
    original_collection = library_app.collection
    original_items = [item.to_dict() for item in original_collection.list_items()]
    original_index = library_app.app.view_functions['index']
    library_app.app.view_functions['index'] = lambda: original_index() + probe
    server = make_server('127.0.0.1', 0, library_app.app, threaded=True, request_handler=QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    try:
        with patch.object(library_app, 'collection', collection), \
             patch('speech_service.load_dotenv', side_effect=AssertionError('dotenv forbidden')), \
             patch.object(library_app, 'synthesize_speech', side_effect=AssertionError('TTS forbidden')) as tts, \
             patch.object(library_app, 'transcribe_pcm', side_effect=AssertionError('STT forbidden')) as stt:
            thread.start()
            profile = Path(__file__).resolve().parent / 'tmp' / 'put-browser-profile'
            output = subprocess.run([str(browser), '--headless', '--mute-audio', '--disable-gpu',
                '--disable-background-networking', '--disable-extensions', '--no-first-run', '--no-default-browser-check',
                '--log-level=3', '--user-data-dir=' + str(profile), '--virtual-time-budget=20000', '--dump-dom',
                f'http://127.0.0.1:{server.server_port}/'], capture_output=True, text=True,
                encoding='utf-8', errors='replace', timeout=40)
            match = re.search(r'<pre id="put-browser-result">(.*?)</pre>', output.stdout, re.S)
            if not match:
                raise SystemExit('No PUT browser report; real microphone verification remains pending.')
            report = json.loads(match.group(1))
            assert report['ok'], report
            tts.assert_not_called(); stt.assert_not_called()
            print(json.dumps(report))
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        library_app.app.view_functions['index'] = original_index
    assert library_app.collection is original_collection
    assert [item.to_dict() for item in original_collection.list_items()] == original_items


if __name__ == '__main__':
    main()
