r"""Real local Flask/Chrome text-panel check; no Azure, microphone, or .env.
Run from Mini-Project-2: .venvScriptspython.exe check_commands_browser.py
Uses an isolated process-local LibraryCollection, never an external running app.
"""
import json
from pathlib import Path
import re
import subprocess
from threading import Thread
from unittest.mock import patch

from werkzeug.serving import WSGIRequestHandler, make_server
import app as library_app
from custom_classes import Book, DVD, LibraryCollection

PROBE = r"""
<script type="module">
const steps = [], errors = [];
const posts = [];
const originalFetch = window.fetch.bind(window);
window.fetch = (url, options = {}) => {
  if (String(url).includes('/api/voice-input') || String(url).includes('/api/tts')) throw new Error('speech-not-allowed-in-text-check');
  if (options.method === 'POST') posts.push({url: String(url), body: JSON.parse(options.body || 'null')});
  return originalFetch(url, options);
};
window.addEventListener('error', e => errors.push(e.error?.name || 'script-error'));
window.addEventListener('unhandledrejection', e => errors.push(e.reason?.name || 'promise-error'));
const el = id => document.getElementById(id);
function check(value, label) { if (!value) throw new Error(label); }
async function waitFor(predicate) {
  for (let i = 0; i < 500; i++) { if (predicate()) return; await new Promise(r => setTimeout(r, 10)); }
  throw new Error('browser-check-timeout');
}
async function command(text, expected, failure = false) {
  el('command-text').value = text;
  el('command-form').dispatchEvent(new Event('submit', {bubbles: true, cancelable: true}));
  await waitFor(() => !el('command-run').disabled && !el(failure ? 'command-error' : 'command-result').hidden);
  check(el(failure ? 'command-error' : 'command-result').textContent.includes(expected), 'unexpected-command-result');
  steps.push(failure ? 'expected-error' : text.split(' ')[0].toLowerCase());
}
try {
  await waitFor(() => el('command-form').getAttribute('aria-busy') === 'false');
  await command('Create item type book title 1984 author Orwell pages three hundred ten', 'ID 4');
  await command('List available books', "4: '1984'");
  check(el('available-filter').value === 'true', 'available-filter-not-synced');
  check(document.querySelector('[data-filter="book"]').getAttribute('aria-pressed') === 'true', 'type-filter-not-synced');
  await command('Get item four', 'Pages: 310');
  check(el('command-result').textContent.includes('ID: 4'), 'missing-id');
  check(el('command-result').textContent.includes('Author / Director: Orwell'), 'missing-author');
  await command('Replace item 4 author Orwell pages 320 title Revised', 'Successfully replaced item 4');
  await command('Update item 4 pages 330', 'Successfully updated item 4');
  await command('Check out item 4', 'has been checked out');
  await command('List checked out books', "4: 'Revised'");
  check(el('available-filter').value === 'false', 'checked-out-filter-not-synced');
  await command('Checkout item 4', 'HTTP 409', true);
  await command('Return item 4', 'Successful return');
  check(el('item-list').children.length === 0, 'mutation-did-not-preserve-filter');
  await command('Delete item 4', 'Successfully deleted item 4');
  await command('Get item 999', 'item 999 was not found', true);
  await command('Check out item 2', 'Handle with care: Do not scratch the disc.');
  await command('Return item 2', 'Successful return');
  await command('List DVDs', "2: 'Inception'");
  await command('Create item, type book, title Test Book, author Test Author, pages 220', 'ID 5');
  await command('Get item 5', 'Author / Director: Test Author');
  check(el('command-result').textContent.includes('Pages: 220'), 'unquoted-detail-mismatch');
  await command('Create item, type book, title "Test Book", author "Test Author", pages 220', 'ID 6');
  await command('Get item 6', 'Author / Director: Test Author');
  check(el('command-result').textContent.includes('Pages: 220'), 'quoted-detail-mismatch');
  for (const example of [
    {text: 'Create item; type: book; title: Test Book; author: Test Author; pages: three hundred and ten.',
      id: 7, fields: {type: 'book', title: 'Test Book', author: 'Test Author', page_count: 310}, detail: 'Pages: 310'},
    {text: 'Create item, type DVD, title Inception, author Christopher Nolan, duration in minutes 148.',
      id: 8, fields: {type: 'dvd', title: 'Inception', author: 'Christopher Nolan', duration: 148}, detail: 'Duration: 148'},
    {text: 'Create item type DVD title Inception author Christopher Nolan Duration. 148 minutes.',
      id: 9, fields: {type: 'dvd', title: 'Inception', author: 'Christopher Nolan', duration: 148}, detail: 'Duration: 148'},
  ]) {
    const before = posts.length;
    await command(example.text, 'ID ' + example.id);
    check(posts.length === before + 1, 'expected-exactly-one-post');
    check(posts[before].url === '/api/items', 'wrong-create-path');
    const payload = posts[before].body;
    check(Object.keys(payload).length === Object.keys(example.fields).length, 'extra-create-fields');
    for (const [key, value] of Object.entries(example.fields)) check(payload[key] === value, 'wrong-create-body-' + key);
    await command('Get item ' + example.id, example.detail);
    const saved = await (await originalFetch('/api/items/' + example.id)).json();
    for (const [key, value] of Object.entries(example.fields)) check(saved[key] === value, 'wrong-saved-field-' + key);
  }
  const beforeInvalid = posts.length;
  await command('Update item 2 duration "in" "minutes" 148', 'quoted', true);
  check(posts.length === beforeInvalid, 'invalid-command-posted');
  check(errors.length === 0, 'javascript-errors');
  const result = document.createElement('pre'); result.id = 'browser-check-result';
  result.textContent = JSON.stringify({ok: true, steps, errors, exactCreateCases: 3, exactCreatePosts: 3}); document.body.append(result);
} catch (error) {
  const result = document.createElement('pre'); result.id = 'browser-check-result';
  result.textContent = JSON.stringify({ok: false, steps, errors, failure: error.message}); document.body.append(result);
}
</script>
"""


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


def main():
    browser = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if not browser.is_file():
        raise SystemExit("Chrome not found; browser check was not run.")
    collection = LibraryCollection()
    collection.add_item(Book("The Hobbit", "Tolkien", 310))
    collection.add_item(DVD("Inception", "Christopher Nolan", 148))
    collection.add_item(Book("1984", "Orwell", 328))
    original = library_app.app.view_functions["index"]
    library_app.app.view_functions["index"] = lambda: original() + PROBE
    server = make_server("127.0.0.1", 0, library_app.app, threaded=True, request_handler=QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    try:
        with patch.object(library_app, "collection", collection):
            thread.start()
            profile = Path(__file__).resolve().parent / "tmp" / "command-browser-profile"
            result = subprocess.run([
                str(browser), "--headless", "--mute-audio", "--disable-gpu", "--disable-background-networking", "--disable-extensions",
                "--no-first-run", "--no-default-browser-check", "--log-level=3", "--user-data-dir=" + str(profile),
                "--virtual-time-budget=20000", "--dump-dom", f"http://127.0.0.1:{server.server_port}/",
            ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=40)
            match = re.search(r'<pre id="browser-check-result">(.*?)</pre>', result.stdout, re.S)
            if not match:
                raise SystemExit("No browser check result. Manual browser behavior is unverified.")
            report = json.loads(match.group(1))
            assert report["ok"], report
            print(json.dumps(report))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        library_app.app.view_functions["index"] = original


if __name__ == "__main__":
    main()
