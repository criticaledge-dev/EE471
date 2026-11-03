// Real Windows Chrome + running Compose website + real Cog. No mocked inference.
// Run from the repo root: node Week-6/task-2/tests/check_browser.mjs
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const profile = resolve(root, "outputs", "chrome-" + randomUUID());
const image = resolve(root, "classifier/test-data/input.jpg");
await mkdir(profile, { recursive: true });
const corrupt = resolve(root, "outputs/corrupt.png");
await writeFile(corrupt, "not an image");
const browser = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
  "--disable-background-networking", "--mute-audio", "--remote-debugging-port=0",
  "--remote-debugging-address=127.0.0.1", `--user-data-dir=${profile}`, "about:blank"
], { windowsHide: true, stdio: "ignore" });
const delay = ms => new Promise(r => setTimeout(r, ms));
let socket;
let nextId = 0;
const pending = new Map();
const errors = [];
const requests = [];
async function wait(predicate, label, limit = 30000) {
  const end = Date.now() + limit;
  while (Date.now() < end) {
    if (await predicate()) return;
    await delay(100);
  }
  throw new Error("Timeout: " + label);
}
function send(method, params = {}) {
  return new Promise((resolveCommand, reject) => {
    const id = ++nextId;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error("CDP timeout: " + method)); }, 20000);
    pending.set(id, { resolve: resolveCommand, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const value = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (value.exceptionDetails) throw new Error("Page evaluation failed: " + value.exceptionDetails.text);
  return value.result.value;
}
async function select(path) {
  const { root: document } = await send("DOM.getDocument");
  const { nodeId } = await send("DOM.querySelector", { nodeId: document.nodeId, selector: "#image" });
  await send("DOM.setFileInputFiles", { nodeId, files: [path] });
}
async function classify() {
  const before = requests.length;
  await evaluate(`document.getElementById('classify').click();
    document.getElementById('classify-form').dispatchEvent(new Event('submit',{cancelable:true,bubbles:true}));`);
  await wait(() => evaluate("!document.getElementById('classify').disabled"), "request finished", 75000);
  assert.equal(requests.length, before + 1, "Duplicate submit must not create two requests");
}

try {
  let port;
  await wait(async () => {
    try { port = Number((await readFile(resolve(profile, "DevToolsActivePort"), "utf8")).split("\n")[0]); return port > 0; }
    catch { return false; }
  }, "Chrome debugging endpoint");
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  socket = new WebSocket(targets.find(t => t.type === "page").webSocketDebuggerUrl);
  await new Promise((yes, no) => { socket.addEventListener("open", yes, { once: true }); socket.addEventListener("error", no, { once: true }); });
  socket.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const task = pending.get(message.id); pending.delete(message.id); clearTimeout(task.timer);
      if (message.error) task.reject(new Error(message.error.message)); else task.resolve(message.result);
    }
    if (message.method === "Runtime.exceptionThrown") errors.push(message.params.exceptionDetails.text);
    if (message.method === "Network.requestWillBeSent" && message.params.request.url.endsWith("/api/classify")) requests.push(message.params.request.method);
  });
  await send("Runtime.enable");
  await send("Network.enable");
  await send("Page.enable");
  await send("Page.addScriptToEvaluateOnNewDocument", { source: `window.__errors=[]; window.__revoked=0;
    window.addEventListener('error',e=>window.__errors.push(e.message));
    window.addEventListener('unhandledrejection',()=>window.__errors.push('unhandledrejection'));
    const revoke=URL.revokeObjectURL.bind(URL); URL.revokeObjectURL=url=>{window.__revoked++;revoke(url)};` });
  await send("Page.navigate", { url: "http://localhost:5063" });
  await wait(() => evaluate("document.getElementById('classify') !== null"), "page initialization");
  assert.equal(requests.length, 0, "No prediction on page load");
  await select(image);
  await wait(() => evaluate("document.getElementById('preview').naturalWidth > 0"), "real preview decoding");
  await classify();
  assert.equal(await evaluate("document.getElementById('result').hidden"), false);
  const direct = await (await fetch("http://127.0.0.1:5064/predictions", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input: { image: "data:image/jpeg;base64," + (await readFile(image)).toString("base64") } })
  })).json();
  assert.equal(direct.status, "succeeded");
  const scores = Object.entries(direct.output).sort((a, b) => b[1] - a[1]);
  const rows = await evaluate("Array.from(document.querySelectorAll('#scores li'),x=>x.textContent)");
  assert.deepEqual(rows, scores.map(([label, score]) => `${label}: ${(score * 100).toFixed(2)}%`));
  assert.equal(await evaluate("document.getElementById('top-class').textContent"), `Top class: ${scores[0][0]} (${(scores[0][1] * 100).toFixed(2)}%)`);
  await select(corrupt);
  assert.equal(await evaluate("document.getElementById('result').hidden"), true, "Selection clears stale results");
  assert.ok(await evaluate("window.__revoked >= 1"));
  await classify();
  assert.equal(await evaluate("document.getElementById('error').hidden"), false);
  assert.equal(await evaluate("document.getElementById('result').hidden"), true);
  await select(image);
  await classify();
  assert.equal(await evaluate("document.getElementById('result').hidden"), false);
  assert.equal(await evaluate("document.getElementById('error').hidden"), true);
  // Empty upload is a real backend request from the page, without bypassing
  // native form validation to manufacture a false UI submission.
  const missing = await evaluate(`(async()=>{const r=await fetch('/api/classify',{method:'POST',body:new FormData()});return {code:r.status,body:await r.json()}})()`);
  assert.equal(missing.code, 400);
  assert.ok(missing.body.error);
  await send("Emulation.setDeviceMetricsOverride", { width: 375, height: 812, deviceScaleFactor: 1, mobile: true });
  assert.ok(await evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "No narrow-screen overflow");
  assert.deepEqual(await evaluate("window.__errors"), []);
  assert.deepEqual(errors, []);
  const report = { ok: true, realBrowser: "Chrome headless", realModel: true, realUploadSubmits: 3,
    duplicateBlocked: true, preview: true, resultsMatchCog: true, corruptRecovery: true,
    missingUpload: true, narrowViewport: true, objectUrlsRevoked: await evaluate("window.__revoked"), errors };
  await writeFile(resolve(root, "outputs/browser-result.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} finally {
  if (socket?.readyState === WebSocket.OPEN) {
    try { await send("Browser.close"); } catch { /* Chrome can close the transport first. */ }
    socket.close();
  }
  for (const task of pending.values()) clearTimeout(task.timer);
  browser.kill();
}
