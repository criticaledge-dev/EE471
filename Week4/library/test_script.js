"use strict";

// Interaction checks with a minimal DOM substitute; these are not browser tests.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const book = { id: 1, type: "book", title: "<img src=x onerror=alert(1)>",
    author: "Writer", page_count: 100, is_available: true };
const dvd = { id: 2, type: "dvd", title: "Film", author: "Director",
    duration: 90, is_available: false };

class Element {
    constructor() {
        this.textContent = "";
        this.hidden = true;
        this.disabled = false;
        this.value = "";
        this.checked = false;
        this.name = "";
        this.dataset = {};
        this.attributes = {};
        this.children = [];
        this.listeners = {};
        this.classes = new Set();
        this.classList = {
            add: (name) => this.classes.add(name),
            toggle: (name, enabled) => enabled ? this.classes.add(name) : this.classes.delete(name),
        };
    }
    set innerHTML(value) { throw new Error("Unsafe HTML assignment: " + value); }
    setAttribute(name, value) { this.attributes[name] = value; }
    addEventListener(name, handler) { this.listeners[name] = handler; }
    trigger(name) { return this.listeners[name]({ preventDefault() {} }); }
    replaceChildren() { this.children = []; }
    append(child) { this.children.push(child); }
    focus() { this.focused = true; }
    querySelector(selector) { return this.parts[selector]; }
}

async function setup(items = [book, dvd]) {
    const ids = ["item-list", "item-template", "loading", "empty", "error", "success",
        "item-count", "item-form", "form-heading", "form-description", "title", "author",
        "type", "detail", "detail-label", "save", "cancel", "available-filter", "refresh"];
    const ui = Object.fromEntries(ids.map((id) => [id, new Element()]));
    ui.type.value = "book";
    ui.detail.name = "page_count";
    ui["item-form"].reset = () => {
        ui.title.value = ui.author.value = ui.detail.value = "";
        ui.type.value = "book";
    };
    const filters = ["", "book", "dvd"].map((value) => {
        const element = new Element();
        element.dataset.filter = value;
        return element;
    });
    ui["item-template"].content = {firstElementChild: {cloneNode() {
        const card = new Element();
        card.parts = Object.fromEntries([".item-title", ".item-author", ".item-type",
            ".item-detail", ".badge", ".state-action", ".edit-action", ".delete-action"]
            .map((selector) => [selector, new Element()]));
        return card;
    }}};
    const replies = [{ status: 200, body: items }];
    const requests = [];
    const context = vm.createContext({
        URLSearchParams,
        document: {
            getElementById: (id) => ui[id],
            querySelectorAll: (selector) => selector === "[data-filter]" ? filters : [
                ...filters, ...["title", "author", "type", "detail", "save", "cancel",
                    "available-filter", "refresh"].map((id) => ui[id]),
                ...ui["item-list"].children.flatMap((card) =>
                    [".state-action", ".edit-action", ".delete-action"].map((key) => card.parts[key])),
            ],
        },
        fetch: async (url, options = {}) => {
            requests.push({ url, ...options });
            let reply = replies.shift();
            assert.ok(reply, "Unexpected request: " + url);
            if (reply instanceof Error) throw reply;
            if (typeof reply === "function") reply = await reply();
            return {status: reply.status, ok: reply.status < 400, json: async () => {
                if (reply.status === 204) throw new Error("204 must not be parsed");
                return reply.body;
            }};
        },
    });
    vm.runInContext(fs.readFileSync(path.join(__dirname, "static/script.js"), "utf8"), context);
    await new Promise((resolve) => setImmediate(resolve));
    return {ui, filters, replies, requests};
}

test("renders user text safely and keeps checked-out delete clickable", async () => {
    const {ui, requests} = await setup();
    assert.equal(requests[0].url, "/api/items");
    const cards = ui["item-list"].children;
    assert.equal(cards[0].parts[".item-title"].textContent, book.title);
    assert.equal(cards[1].parts[".state-action"].textContent, "Return");
    assert.equal(cards[1].parts[".delete-action"].disabled, false);
    assert.equal(ui.loading.hidden, true);
});

test("filters become API query parameters and empty results show a message", async () => {
    const {ui, filters, replies, requests} = await setup();
    replies.push({status: 200, body: [dvd]});
    await filters[2].trigger("click");
    assert.equal(requests.at(-1).url, "/api/items?type=dvd");
    ui["available-filter"].checked = true;
    replies.push({status: 200, body: []});
    await ui["available-filter"].trigger("change");
    assert.equal(requests.at(-1).url, "/api/items?type=dvd&available=true");
    assert.equal(ui.empty.hidden, false);
});

test("create uses POST and current filters are retained on reload", async () => {
    const {ui, filters, replies, requests} = await setup();
    replies.push({status: 200, body: [dvd]});
    await filters[2].trigger("click");
    ui.title.value = "New film";
    ui.author.value = "Creator";
    ui.type.value = "dvd";
    ui.type.trigger("change");
    ui.detail.value = "125";
    replies.push({status: 201, body: {id: 4}}, {status: 200, body: []});
    await ui["item-form"].trigger("submit");
    const save = requests.at(-2);
    assert.equal(save.method, "POST");
    assert.deepEqual(JSON.parse(save.body), {title: "New film", author: "Creator", duration: 125, type: "dvd"});
    assert.equal(requests.at(-1).url, "/api/items?type=dvd");
    assert.equal(ui.success.hidden, false);
    assert.equal(ui.title.value, "");
    assert.equal(ui.save.disabled, false);
});

test("editing uses PATCH without read-only fields and preserves inputs on error", async () => {
    const {ui, replies, requests} = await setup();
    ui["item-list"].children[0].parts[".edit-action"].trigger("click");
    assert.equal(ui.type.disabled, true);
    ui.title.value = "Keep this edit";
    ui.detail.value = "1.5";
    replies.push({status: 400, body: {error: "Page count must be an integer"}});
    await ui["item-form"].trigger("submit");
    assert.equal(requests.at(-1).method, "PATCH");
    assert.equal(requests.at(-1).url, "/api/items/1");
    assert.deepEqual(JSON.parse(requests.at(-1).body), {
        title: "Keep this edit", author: "Writer", page_count: 1.5,
    });
    assert.equal(ui.error.textContent, "Page count must be an integer");
    assert.equal(ui.title.value, "Keep this edit");
    assert.equal(ui.detail.value, "1.5");
    assert.equal(ui.title.disabled, false);
    assert.equal(ui.type.disabled, true);
    assert.equal(ui.save.disabled, false);
    replies.push({status: 200, body: book}, {status: 200, body: [book]});
    await ui["item-form"].trigger("submit");
    assert.equal(ui.type.disabled, false);
    assert.equal(ui.title.value, "");
});

test("DELETE forwards server 409 and handles successful 204 without JSON parsing", async () => {
    const {ui, replies, requests} = await setup();
    replies.push({status: 409, body: {error: "Cannot remove a checked-out item."}});
    await ui["item-list"].children[1].parts[".delete-action"].trigger("click");
    assert.equal(requests.at(-1).method, "DELETE");
    assert.equal(ui.error.textContent, "Cannot remove a checked-out item.");
    for (const card of ui["item-list"].children) {
        for (const selector of [".state-action", ".edit-action", ".delete-action"]) {
            assert.equal(card.parts[selector].disabled, false);
        }
    }
    replies.push({status: 204}, {status: 200, body: [dvd]});
    await ui["item-list"].children[0].parts[".delete-action"].trigger("click");
    assert.equal(ui.success.textContent, "Item deleted.");
    assert.equal(ui.error.hidden, true);
    assert.equal(ui["item-list"].children.length, 1);
});

test("checkout and return use POST and preserve the model success message", async () => {
    const {ui, replies, requests} = await setup();
    replies.push({status: 200, body: {message: "Checkout: handle with care"}},
        {status: 200, body: [book, dvd]});
    await ui["item-list"].children[0].parts[".state-action"].trigger("click");
    assert.equal(requests.at(-2).url, "/api/items/1/checkout");
    assert.equal(requests.at(-2).method, "POST");
    assert.equal(ui.success.textContent, "Checkout: handle with care");
    replies.push({status: 200, body: {message: "Successful return"}},
        {status: 200, body: [book, dvd]});
    await ui["item-list"].children[1].parts[".state-action"].trigger("click");
    assert.equal(requests.at(-2).url, "/api/items/2/return");
});

test("network errors preserve form inputs; pending controls are restored", async () => {
    const {ui, replies} = await setup();
    ui.title.value = "Unsaved title";
    let finish;
    replies.push(() => new Promise((resolve) => { finish = resolve; }));
    const pending = ui.refresh.trigger("click");
    assert.equal(ui.save.disabled, true);
    assert.equal(ui.loading.hidden, false);
    finish({status: 200, body: []});
    await pending;
    assert.equal(ui.save.disabled, false);
    replies.push(new Error("offline"));
    await ui.refresh.trigger("click");
    assert.match(ui.error.textContent, /Cannot reach the server/);
    assert.equal(ui.title.value, "Unsaved title");
    assert.equal(ui.refresh.disabled, false);
    assert.equal(ui.loading.hidden, true);
});

test("successful create followed by failed reload cannot create a duplicate on retry", async () => {
    const {ui, replies, requests} = await setup();
    ui.title.value = "Saved once";
    ui.author.value = "Writer";
    ui.detail.value = "100";
    replies.push({status: 201, body: {...book, id: 4, title: "Saved once"}},
        new Error("reload offline"));
    await ui["item-form"].trigger("submit");
    assert.equal(ui.success.textContent, "Item added.");
    assert.equal(ui.error.hidden, false);
    assert.equal(ui.title.value, "Saved once");
    assert.equal(ui.save.disabled, false);
    assert.equal(ui.type.disabled, true);
    assert.equal(ui.cancel.disabled, false);
    replies.push({status: 200, body: {...book, id: 4}}, {status: 200, body: [book]});
    await ui["item-form"].trigger("submit");
    assert.equal(requests.at(-2).method, "PATCH");
    assert.equal(requests.at(-2).url, "/api/items/4");
    assert.equal(requests.filter((request) => request.method === "POST").length, 1);
    assert.equal(ui.type.disabled, false);
    assert.equal(ui.title.value, "");
});

test("failed filter request cannot leave old items under the newly selected filter", async () => {
    const {ui, filters, replies} = await setup();
    assert.equal(ui["item-list"].children.length, 2);
    replies.push(new Error("offline"));
    await filters[2].trigger("click");
    assert.equal(ui.error.hidden, false);
    assert.equal(ui["item-list"].children.length, 0);
    assert.equal(ui["item-count"].textContent, "");
    assert.equal(ui.empty.hidden, true);
    assert.equal(ui.loading.hidden, true);
    assert.equal(filters[2].disabled, false);
    assert.equal(ui.save.disabled, false);
    assert.equal(ui.refresh.disabled, false);
    replies.push({status: 200, body: [dvd]});
    await ui.refresh.trigger("click");
    assert.equal(ui["item-list"].children.length, 1);
    assert.equal(ui.error.hidden, true);
});
