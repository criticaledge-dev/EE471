import { ChatMicrophone } from "./microphone.mjs";

const byId = id => document.getElementById(id);
const history = byId("history");
const messages = [];
const message = byId("message");
const send = byId("send");
const mic = byId("mic");
let recording = false;
let lastImage = null;

function status(id, text, error = false) {
    const node = byId(id);
    node.textContent = text;
    node.classList.toggle("error", error);
}

function bubble(role, text) {
    byId("empty-chat").hidden = true;
    const box = document.createElement("article");
    box.className = "bubble " + role;
    const name = document.createElement("strong");
    name.textContent = role === "user" ? "SEN" : "ASİSTAN";
    const body = document.createElement("p");
    body.textContent = text;
    box.append(name, body);
    history.append(box);
    history.scrollTop = history.scrollHeight;
    return box;
}

async function post(path, body) {
    const response = await fetch(path, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || "İşlem tamamlanamadı.");
    }
    return response;
}

const microphone = new ChatMicrophone({
    acquire: () => true,
    release: () => {},
    onState: (text, failed) => status("voice-status", text, failed),
    onTranscript: text => { message.value = text; message.focus(); },
    onControls({ startDisabled, stopDisabled }) {
        recording = !stopDisabled;
        mic.disabled = startDisabled && stopDisabled;
        mic.classList.toggle("recording", recording);
        mic.setAttribute("aria-label", recording ? "Kaydı durdur" : "Mikrofon kaydını başlat");
    },
});
mic.addEventListener("click", () => recording ? microphone.stop() : void microphone.start());

byId("chat-form").addEventListener("submit", async event => {
    event.preventDefault();
    const content = message.value.trim();
    if (send.disabled || !content) return;
    send.disabled = true;
    microphone.setInputBusy(true);
    message.readOnly = true;
    status("chat-status", "Asistan yanıt hazırlıyor…");
    const entry = { role: "user", content };
    const attempted = bubble("user", content);
    try {
        const response = await post("/api/chat", { messages: [...messages.slice(-8), entry] });
        const { reply } = await response.json();
        messages.push(entry, { role: "assistant", content: reply });
        bubble("assistant", reply);
        message.value = "";
        status("chat-status", "");
    } catch (error) {
        attempted.remove();
        byId("empty-chat").hidden = history.querySelector(".bubble") !== null;
        status("chat-status", error.message, true);
    } finally {
        send.disabled = false;
        message.readOnly = false;
        microphone.setInputBusy(false);
    }
});

byId("image-form").addEventListener("submit", async event => {
    event.preventDefault();
    const button = byId("generate");
    const prompt = byId("prompt").value.trim();
    if (button.disabled || !prompt) return;
    button.disabled = true;
    status("image-status", "Görsel üretiliyor. İlk çalıştırma daha uzun sürebilir.");
    try {
        const response = await post("/api/image", { prompt });
        const url = URL.createObjectURL(await response.blob());
        const image = byId("art");
        image.src = url;
        image.hidden = false;
        byId("placeholder").hidden = true;
        if (lastImage) URL.revokeObjectURL(lastImage);
        lastImage = url;
        status("image-status", "Görsel hazır.");
    } catch (error) {
        status("image-status", error.message, true);
    } finally {
        button.disabled = false;
    }
});
window.addEventListener("pagehide", () => { if (lastImage) URL.revokeObjectURL(lastImage); });
