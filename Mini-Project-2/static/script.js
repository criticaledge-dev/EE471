"use strict";
import { parseLibraryCommand, describeCommand } from "./command-parser.mjs";
import { executeLibraryCommand } from "./command-runner.mjs";
import { mountVoiceInput } from "./voice-input.mjs";
import { mountSpokenResponses } from "./spoken-responses.mjs";

const ui = Object.fromEntries([
    "item-list", "item-template", "loading", "empty", "error", "success", "item-count",
    "item-form", "form-heading", "form-description", "title", "author", "type",
    "detail", "detail-label", "save", "cancel", "available-filter", "refresh",
    "command-form", "command-text", "command-run", "command-summary", "command-result", "command-error", "command-warning",
].map((id) => [id, document.getElementById(id)]));
const typeFilters = document.querySelectorAll("[data-filter]");
let selectedType = "";
let editingId = null;
let busy = false;
let refreshOnlyCommand = null;
let uncertainCommand = null;
let voiceToken = null;
let microphone = null;
const spoken = mountSpokenResponses({document});

function setBusy(value) {
    busy = value;
    document.querySelectorAll("button, input, select, textarea").forEach((control) => {
        if (!control.dataset.voiceControl && !control.dataset.speechControl) control.disabled = value || voiceToken !== null;
    });
    ui.type.disabled = value || voiceToken !== null || editingId !== null;
    ui["item-form"].setAttribute("aria-busy", String(value || voiceToken !== null));
    ui["command-form"].setAttribute("aria-busy", String(value || voiceToken !== null));
    microphone?.setLibraryBusy(value);
}

function clearMessages() {
    for (const name of ["error", "success"]) {
        ui[name].textContent = "";
        ui[name].hidden = true;
    }
}

function showMessage(name, message) {
    ui[name].textContent = message;
    ui[name].hidden = false;
}

async function apiRequest(url, options = {}) {
    let response;
    try {
        response = await fetch(url, options);
    } catch {
        const mutation = options.method && options.method !== "GET";
        throw Object.assign(new Error("Cannot reach the server. Check your connection and try again."
            + (mutation ? " The operation may have been applied; check the collection before retrying." : "")), { uncertain: Boolean(mutation) });
    }
    // DELETE success has no body and must never be parsed as JSON.
    if (response.status === 204) return null;
    let data;
    try {
        data = await response.json();
    } catch {
        throw Object.assign(new Error("The server returned an unreadable response. Please refresh and try again."),
            { status: response.status, uncertain: Boolean(response.ok && options.method && options.method !== "GET") });
    }
    if (!response.ok) throw Object.assign(new Error(data.error || `Request failed (${response.status}).`), { status: response.status });
    return data;
}

async function runAction(action, token = null) {
    if (busy || voiceToken !== null && token !== voiceToken) return;
    clearMessages();
    setBusy(true);
    try {
        return await action();
    } catch (error) {
        showMessage("error", error.message);
    } finally {
        setBusy(false);
    }
}

function syncDetailField() {
    const isBook = ui.type.value === "book";
    ui["detail-label"].textContent = isBook ? "Page count" : "Duration (minutes)";
    ui.detail.name = isBook ? "page_count" : "duration";
    ui.detail.placeholder = isBook ? "e.g. 310" : "e.g. 148";
}

function resetForm() {
    editingId = null;
    ui["item-form"].reset();
    ui.type.disabled = busy;
    ui["form-heading"].textContent = "Add an item";
    ui["form-description"].textContent = "Build your collection, one item at a time.";
    ui.save.textContent = "Add item";
    syncDetailField();
}

function setEditingMode(itemId) {
    editingId = itemId;
    ui.type.disabled = true;
    ui["form-heading"].textContent = "Edit item";
    ui["form-description"].textContent = "Update the details below. Item type stays the same.";
    ui.save.textContent = "Save changes";
}

function editItem(item) {
    if (busy || voiceToken !== null) return;
    clearMessages();
    setEditingMode(item.id);
    ui.title.value = item.title;
    ui.author.value = item.author;
    ui.type.value = item.type;
    syncDetailField();
    ui.detail.value = item.type === "book" ? item.page_count : item.duration;
    ui.title.focus();
}

function renderItems(items, limit = Infinity) {
    ui["item-list"].replaceChildren();
    for (const item of items.slice(0, limit)) {
        const card = ui["item-template"].content.firstElementChild.cloneNode(true);
        card.querySelector(".item-title").textContent = item.title;
        card.querySelector(".item-author").textContent = item.author;
        card.querySelector(".item-type").textContent = item.type === "book" ? "Book" : "DVD";
        card.querySelector(".item-detail").textContent = item.type === "book"
            ? `${item.page_count} pages` : `${item.duration} min`;
        const badge = card.querySelector(".badge");
        badge.textContent = item.is_available ? "Available" : "Checked out";
        badge.classList.add(item.is_available ? "available" : "checked-out");
        const stateButton = card.querySelector(".state-action");
        stateButton.textContent = item.is_available ? "Checkout" : "Return";
        stateButton.classList.toggle("primary", !item.is_available);
        stateButton.setAttribute("aria-label", `${stateButton.textContent} ${item.title}`);
        stateButton.addEventListener("click", () => runAction(async () => {
            const action = item.is_available ? "checkout" : "return";
            const data = await apiRequest(`/api/items/${item.id}/${action}`, { method: "POST" });
            showMessage("success", data.message);
            await refreshItems();
        }));
        const editButton = card.querySelector(".edit-action");
        editButton.setAttribute("aria-label", `Edit ${item.title}`);
        editButton.addEventListener("click", () => editItem(item));
        const deleteButton = card.querySelector(".delete-action");
        deleteButton.setAttribute("aria-label", `Delete ${item.title}`);
        // Availability rules belong to the server; deletion remains clickable.
        deleteButton.addEventListener("click", () => runAction(async () => {
            await apiRequest(`/api/items/${item.id}`, { method: "DELETE" });
            if (editingId === item.id) resetForm();
            showMessage("success", "Item deleted.");
            await refreshItems();
        }));
        ui["item-list"].append(card);
    }
    ui.empty.hidden = items.length !== 0;
    const availableCount = items.filter((item) => item.is_available).length;
    ui["item-count"].textContent = `${items.length} items / ${availableCount} available in this view`;
    if (items.length > limit) ui["item-count"].textContent += `. Showing first ${limit} cards.`;
}

async function refreshItems({ limit = Infinity } = {}) {
    const query = new URLSearchParams();
    if (selectedType) query.set("type", selectedType);
    if (ui["available-filter"].value) query.set("available", ui["available-filter"].value);
    const suffix = query.size ? `?${query}` : "";
    ui.loading.hidden = false;
    ui.empty.hidden = true;
    ui["item-list"].replaceChildren();
    ui["item-count"].textContent = "";
    ui["item-list"].setAttribute("aria-busy", "true");
    try {
        const items = await apiRequest(`/api/items${suffix}`);
        renderItems(items, limit);
        return items;
    } finally {
        ui.loading.hidden = true;
        ui["item-list"].setAttribute("aria-busy", "false");
    }
}

ui["item-form"].addEventListener("submit", (event) => {
    event.preventDefault();
    return runAction(async () => {
        const fields = {
            title: ui.title.value,
            author: ui.author.value,
            [ui.detail.name]: ui.detail.value === "" ? null : Number(ui.detail.value),
        };
        const isEditing = editingId !== null;
        if (!isEditing) fields.type = ui.type.value;
        const savedItem = await apiRequest(isEditing ? `/api/items/${editingId}` : "/api/items", {
            method: isEditing ? "PATCH" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(fields),
        });
        // Remember a successful create even if the subsequent GET fails.
        if (!isEditing) setEditingMode(savedItem.id);
        showMessage("success", isEditing ? "Changes saved." : "Item added.");
        await refreshItems();
        resetForm();
    });
});

ui.type.addEventListener("change", syncDetailField);
ui.cancel.addEventListener("click", () => {
    if (busy || voiceToken !== null) return;
    resetForm();
    clearMessages();
});
typeFilters.forEach((button) => button.addEventListener("click", () => {
    if (busy || voiceToken !== null) return;
    selectedType = button.dataset.filter;
    typeFilters.forEach((filter) => filter.setAttribute("aria-pressed", String(filter === button)));
    return runAction(refreshItems);
}));
ui["available-filter"].addEventListener("change", () => runAction(refreshItems));
ui.refresh.addEventListener("click", () => runAction(refreshItems));

function setCommandFilters(filters) {
    selectedType = filters.type || "";
    ui["available-filter"].value = filters.available === null ? "" : String(filters.available);
    typeFilters.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.filter === selectedType)));
}

function showCommandResult(result) {
    const output = result.ok ? ui["command-result"] : ui["command-error"];
    output.textContent = result.responseText;
    output.hidden = false;
    if (result.ok && result.command.action === "get") {
        const item = result.data;
        output.textContent += `\n\nID: ${item.id}\nType: ${item.type}\nTitle: ${item.title}\nAuthor / Director: ${item.author}\n`
            + (item.type === "book" ? `Pages: ${item.page_count}` : `Duration: ${item.duration} minutes`)
            + `\nStatus: ${item.is_available ? "Available" : "Checked out"}`;
    }
    if (result.warning) {
        ui["command-warning"].textContent = result.warning;
        ui["command-warning"].hidden = false;
    }
}

function clearCommandFeedback() {
    for (const id of ["command-result", "command-error", "command-warning"]) {
        ui[id].textContent = ""; ui[id].hidden = true;
    }
    ui["command-summary"].textContent = "";
}

// Shared text/transcript entry point. It never receives microphone or Azure data directly.
export async function runCommandText(text, { voiceToken: token = null, signal } = {}) {
    if (busy || voiceToken !== null && token !== voiceToken) return { ok: false, busy: true, responseText: "Another library operation is in progress." };
    if (signal?.aborted) return { ok: false, canceled: true, responseText: "Command canceled before execution." };
    const speechTicket = spoken?.generation;
    const present = (result, speak = true) => {
        if (signal?.aborted) return;
        showCommandResult(result);
        spoken?.notify(result.responseText, result.warning, speak ? speechTicket : -1);
    };
    return runAction(async () => {
        clearCommandFeedback();
        let command;
        try { command = parseLibraryCommand(text); }
        catch (error) {
            const result = { ok: false, stage: "parser", responseText: "Sorry, " + error.message, warning: "" };
            present(result); return result;
        }
        ui["command-summary"].textContent = describeCommand(command);
        if (uncertainCommand?.text === text) {
            present(uncertainCommand.result, false); return uncertainCommand.result;
        }
        if (refreshOnlyCommand?.text === text) {
            const result = { ...refreshOnlyCommand.result };
            try { await refreshItems(); result.warning = ""; refreshOnlyCommand = null; }
            catch { /* Previous write succeeded: only refresh was attempted. */ }
            present(result, false); return result;
        }
        const result = await executeLibraryCommand(command, {
            apiRequest: (url, options = {}) => apiRequest(url, signal ? { ...options, signal } : options),
            refreshItems, setFilters: setCommandFilters, signal,
            onMutation(done) { if (done.action === "delete" && editingId === done.id) resetForm(); },
        });
        if (result.ok && result.warning) refreshOnlyCommand = { text, result };
        if (result.uncertain) uncertainCommand = { text, result };
        result.stage = result.ok ? "result" : "api";
        present(result);
        return result;
    }, token);
}

ui["command-form"].addEventListener("submit", event => {
    event.preventDefault();
    return runCommandText(ui["command-text"].value);
});
microphone = mountVoiceInput({ document, runCommandText,
    onFailure(message) { spoken?.notify(message); },
    acquire() {
        if (busy || voiceToken !== null) return null;
        spoken?.setMicrophone(true);
        clearMessages(); clearCommandFeedback();
        voiceToken = {}; setBusy(busy); return voiceToken;
    },
    release(token) { if (token === voiceToken) { voiceToken = null; setBusy(busy); spoken?.setMicrophone(false); } },
});
void runAction(refreshItems);
