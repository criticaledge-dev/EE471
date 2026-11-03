// Pure text -> command conversion. No DOM, fetch, collection or side effects.
const units = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split(" ");
const tens = { twenty: 20, thirty: 30, forty: 40, fifty: 50, sixty: 60, seventy: 70, eighty: 80, ninety: 90 };
const scales = { thousand: 1000n, million: 1000000n, billion: 1000000000n, trillion: 1000000000000n, quadrillion: 1000000000000000n };
const labels = new Set(["type", "title", "author", "page", "pages", "duration"]);
const forbidden = new Set(["id", "is_available", "page_count", "director", "publisher", "isbn", "year", "available", "status"]);
const extraCommand = /\b(?:create\s+item|list\s+(?:items|books|dvds|available|checked)|get\s+item|replace\s+item|update\s+item|delete\s+item|check\s*out\s+item|return\s+item)\b/i;
const fail = message => { throw new Error(message); };

function fieldAt(tokens, index) {
    const token = tokens[index];
    if (token?.kind !== "word") return null;
    // Only the final word of a known numeric label may carry a structural dot.
    // Never rewrite source/value tokens (e.g. J.D., decimal numbers, quoted text).
    for (const [words, name] of [
        [["duration", "in", "minutes"], "duration"], [["page", "count"], "pages"],
        [["duration"], "duration"], [["pages"], "pages"], [["page"], "pages"],
    ]) {
        const matches = words.every((word, offset) => tokens[index + offset]?.kind === "word"
            && (tokens[index + offset].value.toLowerCase() === word
                || offset === words.length - 1 && tokens[index + offset].value.toLowerCase() === word + "."));
        if (matches) return {name, width: words.length, numeric: true,
            dotted: tokens[index + words.length - 1].value.endsWith(".")};
    }
    const name = token.value.toLowerCase();
    if (!labels.has(name)) return null;
    return { name, width: 1 };
}

// Only a terminal sentence dot at a known field boundary is removable.
// Internal/initial dots (J.D., J., 3.5) are deliberately not normalized here.
function withoutBoundaryDot(value) {
    const last = value.split(/\s+/).at(-1);
    return /^(?:[\p{L}\p{N}][\p{L}\p{N}'’_-]+|\d)\.$/u.test(last) ? value.slice(0, -1) : value;
}

export function positiveInteger(text) {
    let value = text.trim().toLowerCase();
    if (value.includes(",")) {
        if (!/^[1-9]\d{0,2}(?:,\d{3})+$/.test(value)) return fail("Use correctly grouped thousands, for example 1,000 or 12,345,678.");
        value = value.replaceAll(",", "");
    }
    if (/^\d+$/.test(value)) {
        const number = Number(value);
        if (Number.isSafeInteger(number) && number > 0) return number;
        return fail("ID, pages and duration must be positive safe integers.");
    }
    const words = value.replace(/([a-z])-([a-z])/g, "$1 $2").split(/\s+/);
    function below100(part) {
        if (part.length === 1 && units.includes(part[0])) return units.indexOf(part[0]);
        if (part.length === 1 && Object.hasOwn(tens, part[0])) return tens[part[0]];
        if (part.length === 2 && Object.hasOwn(tens, part[0]) && units.indexOf(part[1]) > 0 && units.indexOf(part[1]) < 10) {
            return tens[part[0]] + units.indexOf(part[1]);
        }
        return fail("Use digits or an unambiguous English cardinal number.");
    }
    function below1000(part) {
        if (part[1] !== "hundred") return below100(part);
        const digit = units.indexOf(part[0]);
        if (digit < 1 || digit > 9) return fail("Use one to nine before hundred.");
        let rest = part.slice(2);
        if (!rest.length) return digit * 100;
        if (rest[0] === "and") rest = rest.slice(1);
        const tail = below100(rest);
        if (!tail) return fail("Invalid number after hundred.");
        return digit * 100 + tail;
    }
    let total = 0n, previous = 1000000000000000000n, group = [];
    for (const word of words) {
        if (Object.hasOwn(scales, word)) {
            const scale = scales[word];
            const amount = below1000(group);
            if (!amount || scale >= previous) return fail("Number scales must be in descending order.");
            total += BigInt(amount) * scale; previous = scale; group = [];
        } else group.push(word);
    }
    if (group.length) {
        if (total && group[0] === "and") group = group.slice(1);
        const amount = below1000(group);
        if (!amount) return fail("Use a positive number without redundant zero groups.");
        total += BigInt(amount);
    }
    if (total <= 0n || total > BigInt(Number.MAX_SAFE_INTEGER)) return fail("ID, pages and duration must be positive safe integers.");
    return Number(total);
}

// Double-quoted JSON strings protect literal commas and comma-free field words.
function tokenize(text) {
    const tokens = [];
    for (let i = 0; i < text.length;) {
        if (/\s/.test(text[i])) { i++; continue; }
        if (/[,;:]/.test(text[i])) { const value = text[i]; tokens.push({ kind: value === ":" ? "colon" : "comma", value, start: i, end: ++i }); continue; }
        const start = i;
        // Keep numeric grouping intact; numeric validation rejects malformed groups.
        const grouped = /^\d+(?:,\d+)+/.exec(text.slice(i));
        if (grouped) {
            i += grouped[0].length;
            tokens.push({ kind: "word", value: grouped[0], start, end: i });
            continue;
        }
        if (text[i] === '"') {
            i++;
            while (i < text.length) {
                if (text[i] === "\\") { i += 2; continue; }
                if (text[i++] === '"') break;
            }
            let value;
            try { value = JSON.parse(text.slice(start, i)); } catch { return fail("Close quoted title/author values using valid double quotes."); }
            if (typeof value !== "string") return fail("Invalid quoted value.");
            tokens.push({ kind: "quoted", value, start, end: i });
        } else {
            while (i < text.length && !/[\s,;:"]/.test(text[i])) i++;
            tokens.push({ kind: "word", value: text.slice(start, i), start, end: i });
        }
    }
    return tokens;
}

export function parseLibraryCommand(input) {
    if (typeof input !== "string" || !input.trim() || input.length > 2000) return fail("Enter one English command (at most 2000 characters).");
    const text = input.trim().replace(/[.!?;:]+$/, "").trim();
    const command = { action: "", id: null, fields: {}, filters: { type: null, available: null } };
    const list = /^list\s+(?:(available|checked\s+out)\s+)?(items|books|dvds)$/i.exec(text);
    if (list) {
        command.action = "list";
        command.filters.type = ({ items: null, books: "book", dvds: "dvd" })[list[2].toLowerCase()];
        command.filters.available = list[1] ? list[1].toLowerCase() === "available" : null;
        return command;
    }
    const simple = /^(get|delete|check\s+out|checkout|return)\s+item\s+([\s\S]+)$/i.exec(text);
    if (simple) {
        command.action = /^check/i.test(simple[1]) ? "checkout" : simple[1].toLowerCase();
        command.id = positiveInteger(simple[2]);
        return command;
    }
    const head = /^(create|replace|update)\s+item\b/i.exec(text);
    if (!head) return fail("Unknown command. Use Create, List, Get, Replace, Update, Delete, Check out or Return.");
    command.action = ({ create: "create", replace: "replace", update: "update" })[head[1].toLowerCase()];
    const tokens = tokenize(text.slice(head[0].length));
    // A colon immediately after a complete field label introduces its value.
    // Other colons delimit sections, like commas/semicolons. Quoted text is opaque.
    const labelColons = new Set();
    for (let i = 0; i < tokens.length; i++) {
        const label = fieldAt(tokens, i);
        if (label && tokens[i + label.width]?.kind === "colon") labelColons.add(i + label.width);
    }
    tokens.forEach((token, i) => { if (token.kind === "colon" && !labelColons.has(i)) token.kind = "comma"; });
    const commaMode = tokens.some(token => token.kind === "comma");
    const source = text.slice(head[0].length);
    const quotedFields = new Set();
    const sentenceBoundedFields = new Set();
    let pos = 0;
    const dotBeforeField = index => tokens[index]?.kind === "word" && tokens[index].value === "."
        && (fieldAt(tokens, index + 1) || tokens[index + 1]?.kind === "comma" && fieldAt(tokens, index + 2));
    const nextField = index => fieldAt(tokens, index) || tokens[index]?.kind === "comma" && fieldAt(tokens, index + 1)
        || dotBeforeField(index);
    if (command.action !== "create") {
        const firstField = tokens.findIndex((token, index) => token.kind === "comma" || fieldAt(tokens, index)
            || token.kind === "word" && forbidden.has(token.value.toLowerCase()));
        const end = firstField < 0 ? tokens.length : firstField;
        const idTokens = tokens.slice(0, end);
        if (idTokens.at(-1)?.value === "." && nextField(end)) idTokens.pop();
        let idText = idTokens.map(token => token.value).join(" ");
        if (end < tokens.length) idText = withoutBoundaryDot(idText);
        command.id = positiveInteger(idText);
        pos = end;
    }
    if (dotBeforeField(pos)) pos++;
    if (tokens[pos]?.kind === "comma") pos++;
    while (pos < tokens.length) {
        const label = fieldAt(tokens, pos);
        if (!label) return fail("Unknown or non-editable field. Use type, title, author, page/pages/page count or duration as appropriate.");
        const name = label.name;
        pos += label.width;
        if (!label.dotted && (tokens[pos]?.kind === "colon"
            || label.numeric && tokens[pos]?.kind === "word" && tokens[pos].value === ".")) pos++;
        if (name === "type" && command.action !== "create") return fail("Replace/Update cannot change type.");
        const key = name === "pages" ? "page_count" : name;
        if (Object.hasOwn(command.fields, key)) return fail("Duplicate field: " + name + ". Quote literal field words inside a title or author.");
        const start = pos;
        while (pos < tokens.length) {
            const token = tokens[pos];
            if (dotBeforeField(pos) && (!commaMode || tokens[pos + 1]?.kind === "comma")) break;
            if (token.kind === "comma" || !commaMode && (fieldAt(tokens, pos)
                || token.kind === "word" && forbidden.has(token.value.toLowerCase()))) break;
            pos++;
        }
        const valueTokens = tokens.slice(start, pos);
        if (!valueTokens.length) return fail("Missing value for " + name + ".");
        const quoted = valueTokens.some(token => token.kind === "quoted");
        if (quoted && (valueTokens.length !== 1 || !["title", "author"].includes(name))) return fail("Use a single quoted string only for title or author.");
        let value = quoted ? valueTokens[0].value : source.slice(valueTokens[0].start, valueTokens.at(-1).end).trim();
        if (!commaMode && dotBeforeField(pos)) sentenceBoundedFields.add(key);
        if (!quoted && nextField(pos)) {
            const clean = withoutBoundaryDot(value);
            if (!commaMode && clean !== value) sentenceBoundedFields.add(key);
            value = clean;
        }
        if (!value.trim()) return fail("Title and author must not be empty.");
        // In comma mode the section boundary is explicit. Words such as "Author"
        // inside a title/name are data, never another label or an ambiguity.
        if (quoted) quotedFields.add(key);
        if (!quoted && (extraCommand.test(value) || /\b\w+:/.test(value))) return fail("Ambiguous value or multiple commands. Use one command; quote literal title/author text.");
        const numericValue = name === "duration" ? value.replace(/\s+minutes?$/i, "").trim() : value;
        command.fields[key] = name === "pages" || name === "duration" ? positiveInteger(numericValue)
            : name === "type" ? value.toLowerCase() : value;
        if (dotBeforeField(pos)) pos++;
        if (tokens[pos]?.kind === "comma") {
            pos++;
            if (pos === tokens.length) return fail("Missing field after comma.");
        }
    }
    const fields = command.fields;
    if (!commaMode && command.action === "update" && fields.title !== undefined && fields.author !== undefined
        && !quotedFields.has("title") && !quotedFields.has("author")
        && !sentenceBoundedFields.has(Object.keys(fields).find(key => ["title", "author"].includes(key)))) {
        return fail("Ambiguous comma-free title/author boundary. Separate the fields with commas or quote the title/author value.");
    }
    if (fields.page_count !== undefined && fields.duration !== undefined) return fail("Use pages for a book or duration for a DVD, not both.");
    if (command.action === "create") {
        if (!["book", "dvd"].includes(fields.type)) return fail("Create requires type book or DVD.");
        const detail = fields.type === "book" ? "page_count" : "duration";
        if (Object.keys(fields).length !== 4 || !fields.title || !fields.author || fields[detail] === undefined) return fail("Create requires type, title, author and the correct pages/duration field.");
    } else if (command.action === "replace") {
        if (Object.keys(fields).length !== 3 || !fields.title || !fields.author || fields.page_count === undefined && fields.duration === undefined) return fail("Replace requires title, author and pages or duration.");
    } else if (!Object.keys(fields).length) return fail("Update requires at least one editable field.");
    return command;
}

export function describeCommand(command) {
    if (command.action === "list") return `List ${command.filters.available === null ? "all states" : command.filters.available ? "available" : "checked out"} ${command.filters.type || "items"}.`;
    return `${command.action.toUpperCase()} ${command.id === null ? command.fields.type : "item " + command.id}`
        + (Object.keys(command.fields).length ? ": " + JSON.stringify(command.fields) : ".");
}
