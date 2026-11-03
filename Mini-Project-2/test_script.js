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

async function setup(items = [book, dvd], {voiceEnvironment, speechEnvironment} = {}) {
    const { parseLibraryCommand, describeCommand } = await import("./static/command-parser.mjs");
    const { executeLibraryCommand } = await import("./static/command-runner.mjs");
    const { mountVoiceInput } = await import("./static/voice-input.mjs");
    const { mountSpokenResponses } = await import("./static/spoken-responses.mjs");
    const ids = ["item-list", "item-template", "loading", "empty", "error", "success",
        "item-count", "item-form", "form-heading", "form-description", "title", "author",
        "type", "detail", "detail-label", "save", "cancel", "available-filter", "refresh",
        "command-form", "command-text", "command-run", "command-summary", "command-result", "command-error", "command-warning"];
    if (voiceEnvironment) ids.push("voice-start", "voice-stop", "voice-cancel", "voice-status", "voice-error", "voice-transcript");
    if (speechEnvironment) ids.push('spoken-enabled', 'spoken-play', 'spoken-stop', 'spoken-status', 'spoken-error', 'spoken-text');
    const ui = Object.fromEntries(ids.map((id) => [id, new Element()]));
    if (voiceEnvironment) for (const name of ["start", "stop", "cancel"]) ui["voice-" + name].dataset.voiceControl = name;
    if (speechEnvironment) for (const name of ['enabled', 'play', 'stop']) ui['spoken-' + name].dataset.speechControl = name;
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
    const fetchMock = async (url, options = {}) => {
        requests.push({ url, ...options });
        let reply = replies.shift();
        assert.ok(reply, "Unexpected request: " + url);
        if (reply instanceof Error) throw reply;
        if (typeof reply === "function") reply = await reply();
        return {status: reply.status, ok: reply.status < 400, json: async () => {
            if (reply.status === 204) throw new Error("204 must not be parsed");
            return reply.body;
        }};
    };
    let microphone;
    const context = vm.createContext({
        URLSearchParams,
        parseLibraryCommand, describeCommand, executeLibraryCommand,
        mountSpokenResponses: options => mountSpokenResponses({...options, environment: speechEnvironment}),
        mountVoiceInput: options => (microphone = mountVoiceInput({...options,
            ...(voiceEnvironment ? {environment: {...voiceEnvironment, fetch: fetchMock}} : {})})),
        AbortController,
        document: {
            getElementById: (id) => ui[id],
            querySelectorAll: (selector) => selector === "[data-filter]" ? filters : [
                ...filters, ...["title", "author", "type", "detail", "save", "cancel",
                    "available-filter", "refresh", "command-text", "command-run"].map((id) => ui[id]),
                ...(voiceEnvironment ? [ui["voice-start"], ui["voice-stop"], ui["voice-cancel"]] : []),
                ...(speechEnvironment ? ['enabled', 'play', 'stop'].map(name => ui['spoken-' + name]) : []),
                ...ui["item-list"].children.flatMap((card) =>
                    [".state-action", ".edit-action", ".delete-action"].map((key) => card.parts[key])),
            ],
        },
        fetch: fetchMock,
    });
    // Run the real UI code with its real pure modules injected, not duplicate logic.
    const source = fs.readFileSync(path.join(__dirname, "static/script.js"), "utf8")
        .replace(/^import .*;\r?\n/gm, "").replace(/^export /gm, "");
    vm.runInContext(source, context);
    await new Promise((resolve) => setImmediate(resolve));
    return {ui, filters, replies, requests, microphone, runCommandText: text => context.runCommandText(text)};
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
    ui["available-filter"].value = "true";
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

test("command LIST synchronizes both filters and renders real list results", async () => {
    const {ui, filters, replies, requests, runCommandText} = await setup();
    replies.push({status: 200, body: [dvd]});
    const result = await runCommandText("List checked out DVDs");
    assert.equal(result.ok, true);
    assert.equal(requests.at(-1).url, "/api/items?type=dvd&available=false");
    assert.equal(ui["available-filter"].value, "false");
    assert.equal(filters[2].attributes["aria-pressed"], "true");
    assert.equal(filters[0].attributes["aria-pressed"], "false");
    assert.equal(ui["item-list"].children.length, 1);
    assert.match(ui["command-result"].textContent, /1 item found.*2: 'Film'/);
    ui["available-filter"].value = "true";
    replies.push({status: 200, body: []}); await ui["available-filter"].trigger("change");
    assert.equal(requests.at(-1).url, "/api/items?type=dvd&available=true");
    replies.push({status: 200, body: []}); await runCommandText("List items");
    assert.equal(ui["available-filter"].value, "");
    assert.equal(filters[0].attributes["aria-pressed"], "true");
    assert.match(ui["command-result"].textContent, /No items match/);
});

test("command GET displays all detail fields safely and reports 404/409", async () => {
    const {ui, replies, requests, runCommandText} = await setup();
    replies.push({status: 200, body: book});
    const result = await runCommandText("Get item one");
    assert.equal(requests.at(-1).url, "/api/items/1"); assert.equal(result.ok, true);
    for (const text of ["ID: 1", "Type: book", book.title, "Author / Director: Writer", "Pages: 100", "Status: Available"]) {
        assert.ok(ui["command-result"].textContent.includes(text));
    }
    replies.push({status: 404, body: {error: "Item not found: 999"}});
    await runCommandText("Get item 999");
    assert.equal(ui["command-result"].hidden, true);
    assert.equal(ui["command-error"].textContent, "Sorry, item 999 was not found.");
    replies.push({status: 409, body: {error: "Item is already checked out."}});
    await runCommandText("Check out item 1");
    assert.match(ui["command-error"].textContent, /HTTP 409.*already checked out/);
    assert.equal(ui["command-run"].disabled, false);
});

test("command form CREATE preserves current filters even when new item is hidden", async () => {
    const {ui, replies, requests, runCommandText} = await setup();
    replies.push({status: 200, body: []}); await runCommandText("List checked out books");
    ui["command-text"].value = "Create item type book title New author Writer pages 50";
    replies.push({status: 201, body: {...book, id: 4, title: "New", page_count: 50}}, {status: 200, body: []});
    const result = await ui["command-form"].trigger("submit");
    const post = requests.at(-2);
    assert.equal(post.method, "POST"); assert.equal(post.url, "/api/items");
    assert.deepEqual(JSON.parse(post.body), {type: "book", title: "New", author: "Writer", page_count: 50});
    assert.equal(requests.at(-1).url, "/api/items?type=book&available=false");
    assert.equal(result.ok, true); assert.match(result.responseText, /ID 4/);
    assert.equal(ui["command-error"].hidden, true); assert.equal(ui.empty.hidden, false);
});

test("Replace and Update GET fresh type before one exact PUT/PATCH", async () => {
    for (const [command, method, fields] of [
        ['Replace item 2 author "Director" title Revised duration 150', "PUT", {author: "Director", title: "Revised", duration: 150}],
        ["Update item 2 duration one hundred fifty one", "PATCH", {duration: 151}],
    ]) {
        const {replies, requests, runCommandText} = await setup();
        replies.push({status: 200, body: dvd}, {status: 200, body: {...dvd, ...fields}}, {status: 200, body: [dvd]});
        const result = await runCommandText(command);
        assert.equal(result.ok, true);
        assert.equal(requests[1].url, "/api/items/2"); assert.equal(requests[1].method, undefined);
        assert.equal(requests[2].url, "/api/items/2"); assert.equal(requests[2].method, method);
        assert.deepEqual(JSON.parse(requests[2].body), fields);
        assert.equal(requests.filter(r => r.method === method).length, 1);
    }
});

test("type mismatch, bad parser input and empty PATCH never send mutations", async () => {
    const {replies, requests, runCommandText, ui} = await setup();
    for (const command of ["Update item 1", "Replace item 1 title Missing", "Delete item -3", "Unknown command", "Update item 1 title A title B"]) {
        const before = requests.length; const result = await runCommandText(command);
        assert.equal(result.ok, false); assert.equal(requests.length, before);
        assert.equal(ui["command-result"].hidden, true); assert.ok(result.responseText);
    }
    replies.push({status: 200, body: dvd});
    await runCommandText("Update item 2 pages 330");
    assert.equal(requests.at(-1).method, undefined); assert.equal(requests.length, 2);
    assert.match(ui["command-error"].textContent, /dvd/);
    replies.push({status: 404, body: {error: "Item not found: 999"}});
    const before = requests.length;
    await runCommandText("Update item 999 pages 330");
    assert.equal(requests.length, before + 1); assert.equal(requests.at(-1).method, undefined);
    assert.match(ui["command-error"].textContent, /item 999 was not found/);
});

test("command DELETE consumes 204 without JSON, and checkout preserves DVD warning", async () => {
    const {replies, requests, runCommandText, ui} = await setup();
    replies.push({status: 204}, {status: 200, body: [dvd]});
    let result = await runCommandText("Delete item 1");
    assert.equal(result.ok, true); assert.equal(result.responseText, "Successfully deleted item 1.");
    assert.equal(requests.at(-2).method, "DELETE");
    const message = "Successful checkout. Handle with care: Do not scratch the disc.";
    replies.push({status: 200, body: {message, item: dvd}}, {status: 200, body: [dvd]});
    result = await runCommandText("Checkout item 2");
    assert.match(result.responseText, /Handle with care: Do not scratch the disc/);
    assert.equal(requests.at(-2).url, "/api/items/2/checkout");
    replies.push({status: 200, body: {message: "Successful return", item: {...dvd, is_available: true}}}, {status: 200, body: [dvd]});
    result = await runCommandText("Return item 2");
    assert.equal(requests.at(-2).method, "POST"); assert.equal(requests.at(-2).url, "/api/items/2/return");
    assert.match(ui["command-result"].textContent, /Successful return/);
});

test("command mutation plus reload failure shows success and warning; Run retries only GET", async () => {
    const {ui, replies, requests, runCommandText} = await setup();
    const text = "Create item type book title Saved author Writer pages 10";
    replies.push({status: 201, body: {...book, id: 4, title: "Saved"}}, new Error("offline"));
    const result = await runCommandText(text);
    assert.equal(result.ok, true); assert.equal(ui["command-result"].hidden, false);
    assert.match(ui["command-warning"].textContent, /operation succeeded/);
    assert.equal(ui["command-error"].hidden, true);
    replies.push({status: 200, body: [book]});
    await runCommandText(text);
    assert.equal(requests.filter(request => request.method === "POST").length, 1);
    assert.equal(requests.at(-1).url, "/api/items");
    assert.equal(ui["command-warning"].hidden, true);
});

test("busy command prevents double submission and success waits for API", async () => {
    const {ui, replies, requests, runCommandText} = await setup();
    let finish;
    replies.push(() => new Promise(resolve => { finish = resolve; }), {status: 200, body: []});
    const first = runCommandText("Delete item 1");
    assert.equal(ui["command-run"].disabled, true); assert.equal(ui["command-text"].disabled, true);
    assert.equal(ui["command-result"].hidden, true);
    const second = await runCommandText("Delete item 1");
    assert.equal(second.busy, true); assert.equal(requests.length, 2);
    finish({status: 204}); await first;
    assert.equal(requests.filter(request => request.method === "DELETE").length, 1);
    assert.equal(ui["command-run"].disabled, false);
});

test("ambiguous mutation network outcome is explicit and not automatically resent", async () => {
    const {ui, replies, requests, runCommandText} = await setup();
    replies.push(new Error("offline"));
    const text = "Check out item 1";
    const result = await runCommandText(text);
    assert.equal(result.ok, false); assert.equal(result.uncertain, true);
    assert.match(result.responseText, /may have been applied/);
    const count = requests.length; await runCommandText(text);
    assert.equal(requests.length, count); assert.equal(ui["command-result"].hidden, true);
});

test("HTTP 400 command failure preserves input, hides old success and has responseText", async () => {
    const {ui, replies, runCommandText} = await setup();
    replies.push({status: 200, body: book}); await runCommandText("Get item 1");
    ui["command-text"].value = "Update item 1 pages 330";
    replies.push({status: 200, body: book}, {status: 400, body: {error: "Validation rejected by server"}});
    const result = await ui["command-form"].trigger("submit");
    assert.equal(result.ok, false); assert.match(result.responseText, /HTTP 400.*Validation rejected/);
    assert.equal(ui["command-text"].value, "Update item 1 pages 330");
    assert.equal(ui["command-result"].hidden, true); assert.equal(ui["command-run"].disabled, false);
});

test("quoted and unquoted comma-bound CREATE submit the same exact API payload", async () => {
    const bodies = [];
    for (const text of ['Create item, type book, title Test Book, author Test Author, pages 220',
        'Create item, type book, title "Test Book", author "Test Author", pages 220']) {
        const {ui, replies, requests} = await setup();
        const item = {...book, id: 4, title: "Test Book", author: "Test Author", page_count: 220};
        replies.push({status: 201, body: item}, {status: 200, body: [item]});
        ui["command-text"].value = text;
        const result = await ui["command-form"].trigger("submit");
        assert.equal(result.ok, true);
        const mutations = requests.filter(request => request.method === "POST");
        assert.equal(mutations.length, 1); assert.equal(mutations[0].url, "/api/items");
        bodies.push(JSON.parse(mutations[0].body));
        assert.match(ui["command-result"].textContent, /Test Book.*ID 4/);
    }
    assert.deepEqual(bodies[0], bodies[1]);
    assert.deepEqual(bodies[0], {type: "book", title: "Test Book", author: "Test Author", page_count: 220});
});

test("ambiguous comma-free or invalid field commands send no request before full validation", async () => {
    const {requests, runCommandText, ui} = await setup();
    for (const text of ["Update item 1 title The author of books", "Update item 1 author Jane title New",
        "Create item type book title Test Book author Test Author pages 220",
        "Create item, type book, title X, author Y, pages 220, pages 221",
        "Create item, type book, title X, author Y, pages 220, mystery 1",
        "Create item, type book, title X, pages 220"]) {
        const before = requests.length;
        const result = await runCommandText(text);
        assert.equal(result.ok, false); assert.equal(requests.length, before);
        assert.equal(ui["command-result"].hidden, true); assert.equal(ui["command-run"].disabled, false);
    }
});

test("recognized CREATE/GET/LIST/PUT/PATCH/checkout/return/DELETE use the existing command entry once", async () => {
    const {mockVoiceEnvironment, settle} = await import("./voice-test-helpers.mjs");
    const cases = [
        {text: "Create item type book title The Hobbit author Tolkien pages 310", method: "POST", url: "/api/items", saved: {...book, id: 4}},
        {text: "Get item four", url: "/api/items/4", saved: {...book, id: 4}},
        {text: "List checked out DVDs", url: "/api/items?type=dvd&available=false", saved: [dvd]},
        {text: "Replace item four title Revised author Tolkien pages 320", method: "PUT", url: "/api/items/4", saved: {...book, id: 4, title: "Revised"}, preflight: true},
        {text: "Update item four pages three hundred twenty", method: "PATCH", url: "/api/items/4", saved: {...book, id: 4, page_count: 320}, preflight: true},
        {text: "Check out item four", method: "POST", url: "/api/items/4/checkout", saved: {item: {...book, id: 4, is_available: false}, message: "Successful checkout"}},
        {text: "Return item four", method: "POST", url: "/api/items/4/return", saved: {item: {...book, id: 4}, message: "Successful return"}},
        {text: "Delete item four", method: "DELETE", url: "/api/items/4", saved: null},
    ];
    for (const example of cases) {
        const {env} = mockVoiceEnvironment();
        const h = await setup(undefined, {voiceEnvironment: env});
        h.replies.push({status: 200, body: {text: example.text, language: "en-US"}});
        if (example.preflight) h.replies.push({status: 200, body: {...book, id: 4}});
        h.replies.push({status: example.method === "DELETE" ? 204 : example.method ? 200 : 200, body: example.saved});
        if (example.method) h.replies.push({status: 200, body: []});
        await h.ui["voice-start"].trigger("click");
        assert.equal(h.ui["command-run"].disabled, true); assert.equal(h.ui.save.disabled, true);
        const ignored = await h.runCommandText("Delete item one"); assert.equal(ignored.busy, true);
        h.ui["voice-stop"].trigger("click"); await settle();
        assert.equal(h.ui["voice-transcript"].textContent, example.text);
        assert.equal(h.ui["command-text"].value, example.text);
        assert.equal(h.ui["command-error"].hidden, true, example.text);
        assert.equal(h.requests.filter(r => r.url === "/api/voice-input").length, 1);
        const actions = h.requests.filter(r => r.url !== "/api/voice-input" && r.method);
        assert.equal(actions.length, example.method ? 1 : 0, example.text);
        assert.ok(h.requests.some(r => r.url === example.url && r.method === example.method), example.text);
        assert.equal(h.ui["voice-start"].disabled, false);
    }
});

test("ambiguous transcript is preserved for manual correction, not reported as voice success", async () => {
    const {mockVoiceEnvironment, settle} = await import("./voice-test-helpers.mjs");
    const {env} = mockVoiceEnvironment(); const h = await setup(undefined, {voiceEnvironment: env});
    const text = "Update item four title The author of books";
    h.replies.push({status: 200, body: {text, language: "en-US"}});
    await h.ui["voice-start"].trigger("click"); h.ui["voice-stop"].trigger("click"); await settle();
    assert.equal(h.requests.length, 2); // Initial list + transcript only; no Library lookup/write.
    assert.equal(h.ui["command-text"].value, text);
    assert.match(h.ui["voice-status"].textContent, /manual correction/);
    h.ui["command-text"].value = 'Update item four, title "The author of books"';
    h.replies.push({status: 200, body: {...book, id: 4}}, {status: 200, body: {...book, id: 4, title: "The author of books"}}, {status: 200, body: []});
    await h.ui["command-form"].trigger("submit");
    assert.equal(h.requests.filter(r => r.method === "PATCH").length, 1);
    assert.match(h.ui["voice-status"].textContent, /manual correction/);
});

test("cancel during voice type preflight never sends a subsequent mutation", async () => {
    const {mockVoiceEnvironment, settle} = await import("./voice-test-helpers.mjs");
    const {env, state} = mockVoiceEnvironment(); const h = await setup(undefined, {voiceEnvironment: env});
    let resolveType;
    h.replies.push({status: 200, body: {text: "Update item four pages 320", language: "en-US"}},
        () => new Promise(resolve => { resolveType = resolve; }));
    await h.ui["voice-start"].trigger("click"); h.ui["voice-stop"].trigger("click"); await settle();
    assert.ok(resolveType); assert.equal(h.ui["voice-cancel"].disabled, true);
    state.pageHide(); await settle(); resolveType({status: 200, body: {...book, id: 4}}); await settle();
    assert.equal(h.requests.filter(r => r.method === "PATCH").length, 0);
    assert.equal(h.ui["voice-start"].disabled, false);
});

test("voice mutation success plus refresh failure does not replay the write", async () => {
    const {mockVoiceEnvironment, settle} = await import("./voice-test-helpers.mjs");
    const {env} = mockVoiceEnvironment(); const h = await setup(undefined, {voiceEnvironment: env});
    const text = "Create item, type book, title Test Book, author Test Author, pages 220";
    h.replies.push({status: 200, body: {text, language: "en-US"}}, {status: 201, body: {...book, id: 4}}, new Error("offline"));
    await h.ui["voice-start"].trigger("click"); h.ui["voice-stop"].trigger("click"); await settle();
    assert.equal(h.ui["command-result"].hidden, false); assert.equal(h.ui["command-warning"].hidden, false);
    assert.match(h.ui["voice-status"].textContent, /Command succeeded/);
    h.replies.push({status: 200, body: [book]}); await h.ui["command-form"].trigger("submit");
    assert.equal(h.requests.filter(r => r.url === "/api/items" && r.method === "POST").length, 1);
    assert.equal(h.requests.filter(r => r.url === "/api/voice-input").length, 1);
});

test("microphone/STT and Library errors remain separate and allow another recording", async () => {
    const {mockVoiceEnvironment, settle} = await import("./voice-test-helpers.mjs");
    const {env} = mockVoiceEnvironment(); const h = await setup(undefined, {voiceEnvironment: env});
    h.replies.push({status: 503, body: {error: "Configure SPEECH_KEY and SPEECH_REGION on the server."}});
    await h.ui["voice-start"].trigger("click"); h.ui["voice-stop"].trigger("click"); await settle();
    assert.equal(h.ui["voice-error"].hidden, false); assert.equal(h.ui["command-error"].hidden, true);
    assert.equal(h.requests.length, 2);
    h.replies.push({status: 200, body: {text: "Check out item one", language: "en-US"}}, {status: 409, body: {error: "Item is already checked out."}});
    await h.ui["voice-start"].trigger("click"); h.ui["voice-stop"].trigger("click"); await settle();
    assert.equal(h.ui["voice-error"].hidden, true); assert.match(h.ui["command-error"].textContent, /HTTP 409/);
    assert.equal(h.ui["voice-start"].disabled, false);
});

test("page exit after sending a voice mutation does not claim rollback or retry", async () => {
    const {mockVoiceEnvironment, settle} = await import("./voice-test-helpers.mjs");
    const {env, state} = mockVoiceEnvironment(); const h = await setup(undefined, {voiceEnvironment: env});
    let rejectWrite;
    const text = "Delete item one";
    h.replies.push({status: 200, body: {text, language: "en-US"}}, () => new Promise((_resolve, reject) => { rejectWrite = reject; }));
    await h.ui["voice-start"].trigger("click"); h.ui["voice-stop"].trigger("click"); await settle();
    assert.ok(rejectWrite); state.pageHide(); await settle();
    rejectWrite(new Error("connection closed")); await settle();
    assert.match(h.ui["voice-status"].textContent, /does not undo a mutation/);
    const before = h.requests.length; const result = await h.runCommandText(text);
    assert.equal(result.uncertain, true); assert.equal(h.requests.length, before);
});

test("actual Azure Page transcript sends exactly one correct Library POST", async () => {
    const {mockVoiceEnvironment, settle} = await import("./voice-test-helpers.mjs");
    const {env} = mockVoiceEnvironment(); const h = await setup(undefined, {voiceEnvironment: env});
    const text = "Create Item Type Book Title Hobbit Author Tolkien. Page 310.";
    const fields = {type: "book", title: "Hobbit", author: "Tolkien", page_count: 310};
    h.replies.push({status: 200, body: {text, language: "en-US"}},
        {status: 201, body: {...fields, id: 4, is_available: true}}, {status: 200, body: []});
    await h.ui["voice-start"].trigger("click"); h.ui["voice-stop"].trigger("click"); await settle();
    const posts = h.requests.filter(r => r.url === "/api/items" && r.method === "POST");
    assert.equal(posts.length, 1); assert.deepEqual(JSON.parse(posts[0].body), fields);
    assert.equal(h.ui["voice-transcript"].textContent, text);
    assert.equal(h.ui["command-text"].value, text);
    assert.equal(h.ui["command-error"].hidden, true);
});

test("invalid page-boundary commands make no API request before complete validation", async () => {
    const h = await setup();
    for (const text of ["Create item type book title Hobbit author Tolkien. Page",
        "Create item, type book, title Hobbit, author Tolkien, page 310, pages 320",
        "Update item 3 title The author of books. Page 310",
        "Create item type book title Hobbit. Page 310"]) {
        const before = h.requests.length;
        const result = await h.runCommandText(text);
        assert.equal(result.ok, false); assert.equal(h.requests.length, before);
    }
});

test("long LIST commands cap cards and summaries without losing true count", async () => {
    const {ui, replies, runCommandText} = await setup();
    const items = Array.from({length: 105}, (_, i) => ({...book, id: i + 1, title: "x".repeat(1000)}));
    replies.push({status: 200, body: items});
    const result = await runCommandText("List books");
    assert.equal(ui["item-list"].children.length, 100);
    assert.match(ui["item-count"].textContent, /105 items.*first 100/);
    assert.ok(result.responseText.length < 600);
});

test("all eight tolerant command forms use real form binding and the common parser/runner", async () => {
    const cases = [
        {text: ' CrEaTe\n item; type: book; title: 1984; author: J.D. Salinger; page count: 1,310?!',
            method: 'POST', url: '/api/items', body: {type: 'book', title: '1984', author: 'J.D. Salinger', page_count: 1310}, reply: {status: 201, body: book}},
        {text: 'LIST\n available\t books!', method: 'GET', url: '/api/items?type=book&available=true', reply: {status: 200, body: [book]}},
        {text: 'Get\n item one\n thousand;', method: 'GET', url: '/api/items/1000', reply: {status: 200, body: book}},
        {text: 'Replace item 1: title: Revised: author: Tolkien: pages: three hundred and ten.',
            method: 'PUT', url: '/api/items/1', body: {title: 'Revised', author: 'Tolkien', page_count: 310}, preflight: book, reply: {status: 200, body: book}},
        {text: 'Update item 2; duration in minutes: 148 minutes!', method: 'PATCH', url: '/api/items/2', body: {duration: 148}, preflight: dvd, reply: {status: 200, body: dvd}},
        {text: 'Delete\n item one:', method: 'DELETE', url: '/api/items/1', reply: {status: 204}},
        {text: 'Check\n out item one?!', method: 'POST', url: '/api/items/1/checkout', reply: {status: 200, body: {item: book, message: 'Checked out.'}}},
        {text: 'RETURN\n item one...', method: 'POST', url: '/api/items/1/return', reply: {status: 200, body: {item: book, message: 'Returned.'}}},
    ];
    for (const c of cases) {
        const h = await setup();
        const before = h.requests.length;
        if (c.preflight) h.replies.push({status: 200, body: c.preflight});
        h.replies.push(c.reply);
        if (c.method !== 'GET') h.replies.push({status: 200, body: []});
        h.ui['command-text'].value = c.text;
        const result = await h.ui['command-form'].trigger('submit');
        assert.equal(result.ok, true, c.text);
        const requests = h.requests.slice(before);
        const matches = requests.filter(r => r.url === c.url && (r.method || 'GET') === c.method);
        assert.equal(matches.length, 1, c.text);
        if (c.body) assert.deepEqual(JSON.parse(matches[0].body), c.body);
        assert.equal(requests.filter(r => ['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.method)).length, c.method === 'GET' ? 0 : 1);
    }
});

test("malformed grouping, units and ambiguous delimiter sections send no network requests", async () => {
    const h = await setup();
    for (const text of ['Update item 1; pages: 1,00', 'Update item 2; duration: 148 seconds',
        'Update item 1 title The author of books', 'Update item 1: title: X: publisher: Y',
        'Create item; type: book; title: X; author: Y; pages: 310; page count: 320',
        'Update item 1; title: X; delete item 2', 'Update item 2 duration "in" "minutes" 148']) {
        const before = h.requests.length;
        h.ui['command-text'].value = text;
        const result = await h.ui['command-form'].trigger('submit');
        assert.equal(result.ok, false, text);
        assert.equal(h.requests.length, before, text);
    }
});

test("exact manual failure reports submit one POST each through Command form and shared runner", async () => {
    for (const [text, fields] of [
        ['Create item; type: book; title: Test Book; author: Test Author; pages: three hundred and ten.',
            {type: 'book', title: 'Test Book', author: 'Test Author', page_count: 310}],
        ['Create item, type DVD, title Inception, author Christopher Nolan, duration in minutes 148.',
            {type: 'dvd', title: 'Inception', author: 'Christopher Nolan', duration: 148}],
    ]) {
        const h = await setup();
        h.replies.push({status: 201, body: {...fields, id: 4, is_available: true}}, {status: 200, body: []});
        h.ui['command-text'].value = text;
        const result = await h.ui['command-form'].trigger('submit');
        assert.equal(result.ok, true, text);
        const posts = h.requests.filter(r => r.method === 'POST');
        assert.equal(posts.length, 1);
        assert.equal(posts[0].url, '/api/items');
        assert.deepEqual(JSON.parse(posts[0].body), fields);
    }
});

test('real Duration-dot transcript sends exactly one correct POST via Command; invalid variants send none', async () => {
    const fields = {type: 'dvd', title: 'Inception', author: 'Christopher Nolan', duration: 148};
    for (const text of ['Create item type DVD title Inception author Christopher Nolan Duration. 148 minutes.',
        'Create item type DVD title Inception author Christopher Nolan duration: 148 minutes',
        'Create item type DVD title Inception author Christopher Nolan duration 148 minutes']) {
        const h = await setup();
        h.replies.push({status: 201, body: {...fields, id: 4, is_available: true}}, {status: 200, body: []});
        h.ui['command-text'].value = text;
        assert.equal((await h.ui['command-form'].trigger('submit')).ok, true);
        const posts = h.requests.filter(r => r.method === 'POST');
        assert.equal(posts.length, 1); assert.equal(posts[0].url, '/api/items');
        assert.deepEqual(JSON.parse(posts[0].body), fields);
    }
    const h = await setup();
    for (const text of ['Create item type DVD title Inception author Christopher Nolan Duration.',
        'Create item type DVD title Inception author Christopher Nolan Duration. 1.5 minutes',
        'Update item 3 title The author of books pages. 310', 'Update item 2 duration. -148']) {
        const before = h.requests.length;
        h.ui['command-text'].value = text;
        assert.equal((await h.ui['command-form'].trigger('submit')).ok, false);
        assert.equal(h.requests.length, before);
    }
});

test('both real mixed-separator transcripts reach the shared runner with one exact POST each', async () => {
    const fields = {type: 'book', title: 'Hobbit', author: 'Tolkien', page_count: 500};
    for (const text of ['Create item type book titled Hobbit Author Tolkien, pages 500.',
        'Create Item Type Book Title Hobbit Author Tolkien, Pages 500.']) {
        const h = await setup();
        h.replies.push({status: 201, body: {...fields, id: 4, is_available: true}}, {status: 200, body: []});
        h.ui['command-text'].value = text;
        const result = await h.ui['command-form'].trigger('submit');
        assert.equal(result.ok, true, text);
        const mutations = h.requests.filter(r => ['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.method));
        assert.equal(mutations.length, 1); assert.equal(mutations[0].method, 'POST');
        assert.equal(mutations[0].url, '/api/items');
        assert.deepEqual(JSON.parse(mutations[0].body), fields);
        assert.equal(h.ui['command-error'].hidden, true);
    }
});

test('mixed invalid or ambiguous fields never reach an API preflight or mutation', async () => {
    const h = await setup();
    for (const text of ['Create item type book titled Hobbit Author Tolkien, pages -500',
        'Create item type book titled Hobbit title Other author Tolkien, pages 500',
        'Create item type book title Hobbit, author Tolkien pages 500',
        'Update item 3 pages 500 title The author of books',
        'Create item type book titled Hobbit author Tolkien, unknown 500']) {
        const before = h.requests.length; h.ui['command-text'].value = text;
        const result = await h.ui['command-form'].trigger('submit');
        assert.equal(result.ok, false, text); assert.equal(h.requests.length, before);
    }
});

test('all command results and parser/HTTP errors reach speech once via the shared entry', async () => {
    const {mockSpeech} = await import('./speech-test-helpers.mjs');
    const {settle} = await import('./voice-test-helpers.mjs');
    const cases = [
        ['Create item type book title Hobbit author Tolkien pages 310', [{status: 201, body: {...book, title: 'Hobbit', id: 4}}, {status: 200, body: []}], /created book 'Hobbit'.*ID 4/],
        ['Get item 1', [{status: 200, body: book}], /Item 1.*book.*100 pages.*available/],
        ['List items', [{status: 200, body: []}], /No items/],
        ['Replace item 1 title Revised author Tolkien pages 320', [{status: 200, body: book}, {status: 200, body: book}, {status: 200, body: []}], /replaced item 1/],
        ['Update item 1 pages 320', [{status: 200, body: book}, {status: 200, body: book}, {status: 200, body: []}], /updated item 1/],
        ['Delete item 1', [{status: 204}, {status: 200, body: []}], /deleted item 1/],
        ['Check out item 2', [{status: 200, body: {item: dvd, message: 'Handle with care: Do not scratch the disc.'}}, {status: 200, body: []}], /Do not scratch/],
        ['Return item 2', [{status: 200, body: {item: dvd, message: 'Successful return.'}}, {status: 200, body: []}], /returned.*Successful return/],
        ['Get item 999', [{status: 404, body: {error: 'Not found'}}], /999 was not found/],
        ['Check out item 2', [{status: 409, body: {error: 'Already checked out'}}], /HTTP 409/],
        ['Get item 1', [{status: 400, body: {error: 'Bad input'}}], /HTTP 400/],
        ['Unknown command', [], /Sorry, Unknown command/],
        ['Delete item 1', [new Error('offline')], /may have been applied/],
    ];
    for (const [text, replies, expected] of cases) {
        const speech = mockSpeech(); const h = await setup(undefined, {speechEnvironment: speech.env});
        assert.equal(speech.state.requests.length, 0);
        h.ui['spoken-enabled'].checked = true; h.ui['spoken-enabled'].trigger('change');
        h.replies.push(...replies); h.ui['command-text'].value = text;
        await h.ui['command-form'].trigger('submit'); await settle();
        assert.equal(speech.state.requests.length, 1, text);
        assert.equal(speech.state.requests[0].url, '/api/tts');
        assert.match(JSON.parse(speech.state.requests[0].options.body).text, expected);
    }
});

test('speech waits for API, preserves successful Library result on play failure, and replay never mutates', async () => {
    const {mockSpeech} = await import('./speech-test-helpers.mjs');
    const {settle, deferred} = await import('./voice-test-helpers.mjs');
    const speech = mockSpeech({playError: true}), pending = deferred();
    const h = await setup(undefined, {speechEnvironment: speech.env});
    h.ui['spoken-enabled'].checked = true; h.ui['spoken-enabled'].trigger('change');
    h.replies.push(() => pending.promise, {status: 200, body: []});
    const result = h.runCommandText('Delete item 1'); await settle();
    assert.equal(speech.state.requests.length, 0);
    assert.equal(h.ui['spoken-enabled'].disabled, false); assert.equal(h.ui['spoken-stop'].disabled, false);
    pending.resolve({status: 204}); assert.equal((await result).ok, true); await settle();
    assert.equal(h.ui['command-result'].hidden, false); assert.equal(h.ui['command-error'].hidden, true);
    assert.equal(h.ui['spoken-error'].hidden, false);
    const before = h.requests.length;
    h.ui['spoken-play'].trigger('click'); await settle();
    assert.equal(h.requests.length, before); assert.equal(speech.state.requests.length, 2);
    assert.equal(h.requests.filter(r => r.method === 'DELETE').length, 1);
});

test('refresh warnings are spoken with success once; refresh retry and stale command do not replay speech', async () => {
    const {mockSpeech} = await import('./speech-test-helpers.mjs');
    const {settle, deferred} = await import('./voice-test-helpers.mjs');
    const speech = mockSpeech(), h = await setup(undefined, {speechEnvironment: speech.env});
    h.ui['spoken-enabled'].checked = true; h.ui['spoken-enabled'].trigger('change');
    h.replies.push({status: 204}, new Error('offline'));
    await h.runCommandText('Delete item 1'); await settle();
    assert.match(JSON.parse(speech.state.requests[0].options.body).text, /deleted item 1.*operation succeeded.*could not be refreshed/);
    h.replies.push({status: 200, body: []}); await h.runCommandText('Delete item 1'); await settle();
    assert.equal(speech.state.requests.length, 1); assert.equal(h.requests.filter(r => r.method === 'DELETE').length, 1);
    assert.doesNotMatch(h.ui['spoken-text'].textContent, /could not be refreshed/);
    const pending = deferred(); h.replies.push(() => pending.promise);
    const result = h.runCommandText('Get item 1'); await settle();
    h.ui['spoken-stop'].trigger('click'); pending.resolve({status: 200, body: book}); await result; await settle();
    assert.equal(speech.state.requests.length, 1);
});

test('voice results and STT failures share speech, while microphone cancels old audio before capture', async () => {
    const {mockSpeech} = await import('./speech-test-helpers.mjs');
    const {mockVoiceEnvironment, settle} = await import('./voice-test-helpers.mjs');
    const speech = mockSpeech({autoEnd: false}), voice = mockVoiceEnvironment();
    const h = await setup(undefined, {speechEnvironment: speech.env, voiceEnvironment: voice.env});
    h.ui['spoken-enabled'].checked = true; h.ui['spoken-enabled'].trigger('change');
    h.replies.push({status: 200, body: book}); await h.runCommandText('Get item 1'); await settle();
    h.replies.push({status: 200, body: {text: 'List books', language: 'en-US'}}, {status: 200, body: []});
    await h.ui['voice-start'].trigger('click'); assert.ok(speech.state.audios[0].paused);
    assert.equal(h.ui['spoken-play'].disabled, true);
    h.ui['voice-stop'].trigger('click'); await settle();
    assert.equal(speech.state.requests.length, 2); assert.ok(voice.state.track.stopped);
    h.replies.push({status: 422, body: {error: 'No speech'}});
    await h.ui['voice-start'].trigger('click'); h.ui['voice-stop'].trigger('click'); await settle();
    assert.equal(speech.state.requests.length, 3);
    assert.match(JSON.parse(speech.state.requests[2].options.body).text, /No complete speech/);
    assert.equal(h.ui['voice-error'].hidden, false);
    h.ui['spoken-stop'].trigger('click'); await settle();
});

test('canceled voice transcript cannot trigger speech or mutate; TTS HTTP failure leaves Library success intact', async () => {
    const {mockSpeech, speechReply} = await import('./speech-test-helpers.mjs');
    const {mockVoiceEnvironment, settle, deferred} = await import('./voice-test-helpers.mjs');
    const speech = mockSpeech({fetchReply: () => ({...speechReply(), ok: false})});
    const voice = mockVoiceEnvironment(), pending = deferred();
    const h = await setup(undefined, {speechEnvironment: speech.env, voiceEnvironment: voice.env});
    h.ui['spoken-enabled'].checked = true; h.ui['spoken-enabled'].trigger('change');
    h.replies.push(() => pending.promise);
    await h.ui['voice-start'].trigger('click'); h.ui['voice-stop'].trigger('click'); await settle();
    await h.ui['voice-cancel'].trigger('click');
    pending.resolve({status: 200, body: {text: 'Delete item 1', language: 'en-US'}}); await settle();
    assert.equal(speech.state.requests.length, 0);
    assert.equal(h.requests.filter(r => r.method === 'DELETE').length, 0);
    h.replies.push({status: 204}, {status: 200, body: []});
    const result = await h.runCommandText('Delete item 1'); await settle();
    assert.equal(result.ok, true); assert.equal(h.ui['command-error'].hidden, true);
    assert.equal(h.ui['command-result'].hidden, false); assert.equal(h.ui['spoken-error'].hidden, false);
    const count = h.requests.length; h.ui['spoken-play'].trigger('click'); await settle();
    assert.equal(h.requests.length, count); assert.equal(speech.state.requests.length, 2);
});
