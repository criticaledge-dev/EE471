"use strict";

const ui = Object.fromEntries([
    "item-list", "item-template", "loading", "empty", "error", "success", "item-count",
    "item-form", "form-heading", "form-description", "title", "author", "type",
    "detail", "detail-label", "save", "cancel", "available-filter", "refresh",
].map((id) => [id, document.getElementById(id)]));
const typeFilters = document.querySelectorAll("[data-filter]");
let selectedType = "";
let editingId = null;
let busy = false;

function setBusy(value) {
    busy = value;
    document.querySelectorAll("button, input, select").forEach((control) => {
        control.disabled = value;
    });
    ui.type.disabled = value || editingId !== null;
    ui["item-form"].setAttribute("aria-busy", String(value));
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
        throw new Error("Cannot reach the server. Check your connection and try again.");
    }
    // DELETE success has no body and must never be parsed as JSON.
    if (response.status === 204) return null;
    let data;
    try {
        data = await response.json();
    } catch {
        throw new Error("The server returned an unreadable response. Please refresh and try again.");
    }
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
    return data;
}

async function runAction(action) {
    if (busy) return;
    clearMessages();
    setBusy(true);
    try {
        await action();
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
    if (busy) return;
    clearMessages();
    setEditingMode(item.id);
    ui.title.value = item.title;
    ui.author.value = item.author;
    ui.type.value = item.type;
    syncDetailField();
    ui.detail.value = item.type === "book" ? item.page_count : item.duration;
    ui.title.focus();
}

function renderItems(items) {
    ui["item-list"].replaceChildren();
    for (const item of items) {
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
}

async function refreshItems() {
    const query = new URLSearchParams();
    if (selectedType) query.set("type", selectedType);
    if (ui["available-filter"].checked) query.set("available", "true");
    const suffix = query.size ? `?${query}` : "";
    ui.loading.hidden = false;
    ui.empty.hidden = true;
    ui["item-list"].replaceChildren();
    ui["item-count"].textContent = "";
    ui["item-list"].setAttribute("aria-busy", "true");
    try {
        const items = await apiRequest(`/api/items${suffix}`);
        renderItems(items);
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
    if (busy) return;
    resetForm();
    clearMessages();
});
typeFilters.forEach((button) => button.addEventListener("click", () => {
    if (busy) return;
    selectedType = button.dataset.filter;
    typeFilters.forEach((filter) => filter.setAttribute("aria-pressed", String(filter === button)));
    return runAction(refreshItems);
}));
ui["available-filter"].addEventListener("change", () => runAction(refreshItems));
ui.refresh.addEventListener("click", () => runAction(refreshItems));
void runAction(refreshItems);
