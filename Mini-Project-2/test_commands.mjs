import test from "node:test";
import assert from "node:assert/strict";
import { parseLibraryCommand as parse, positiveInteger } from "./static/command-parser.mjs";
import { executeLibraryCommand as execute, summarizeItems } from "./static/command-runner.mjs";

test("all command families and case-insensitive DVD spelling", () => {
    for (const [text, action, id] of [["Get item 3", "get", 3], ["Delete item three.", "delete", 3],
        ["Check out item 3", "checkout", 3], ["Checkout item THREE!", "checkout", 3], ["Return item 3", "return", 3]]) {
        const c = parse(text); assert.equal(c.action, action); assert.equal(c.id, id);
    }
    assert.deepEqual(parse("Create item, type book, title The Hobbit, author Tolkien, pages 310").fields,
        { type: "book", title: "The Hobbit", author: "Tolkien", page_count: 310 });
    assert.deepEqual(parse("Create item, type DVD, title Inception, author Christopher Nolan, duration 148").fields,
        { type: "dvd", title: "Inception", author: "Christopher Nolan", duration: 148 });
});

test("all nine list commands and availability false", () => {
    for (const [word, type] of [["items", null], ["books", "book"], ["DVDs", "dvd"]]) {
        for (const [state, available] of [["", null], ["available ", true], ["checked out ", false]]) {
            assert.deepEqual(parse("List " + state + word).filters, { type, available });
        }
    }
});

test('both real mixed-separator transcripts normalize to the same book fields', () => {
    const expected = {type: 'book', title: 'Hobbit', author: 'Tolkien', page_count: 500};
    for (const text of ['Create item type book titled Hobbit Author Tolkien, pages 500.',
        'Create Item Type Book Title Hobbit Author Tolkien, Pages 500.']) {
        assert.deepEqual(parse(text).fields, expected, text);
    }
});

test('local field boundaries support mixed sections, field order, punctuation and number words', () => {
    const expected = {type: 'book', title: 'Hobbit', author: 'Tolkien', page_count: 500};
    for (const text of ['Create item, type book title Hobbit author Tolkien pages 500',
        'Create item type book title Hobbit, author Tolkien, pages 500',
        'Create item type book, title Hobbit, author Tolkien, pages 500',
        'Create item type book titled Hobbit author Tolkien; pages five hundred',
        'Create item; type: book title: Hobbit author: Tolkien; page count. 500',
        'Create item type book title "Hobbit" author "Tolkien", pages 500',
        'Create item pages five hundred, type book titled Hobbit author Tolkien']) {
        assert.deepEqual(parse(text).fields, expected, text);
    }
    assert.deepEqual(parse('Replace item three, page count five hundred titled Hobbit author Tolkien').fields,
        {page_count: 500, title: 'Hobbit', author: 'Tolkien'});
    assert.deepEqual(parse('Replace item three titled "Hobbit" author Tolkien, page count five hundred').fields,
        {title: 'Hobbit', author: 'Tolkien', page_count: 500});
    assert.deepEqual(parse('Update item 3 pages 500, titled Hobbit').fields, {page_count: 500, title: 'Hobbit'});
    assert.deepEqual(parse('Create item type DVD title Inception author Nolan, duration in minutes. 148 minutes').fields,
        {type: 'dvd', title: 'Inception', author: 'Nolan', duration: 148});
});

test('delimiter-start text sections and quoted atoms preserve literal labels and dotted names in mixed commands', () => {
    assert.deepEqual(parse('Create item type book, titled The author of title pages titled, author Title Author Pages, pages 500').fields,
        {type: 'book', title: 'The author of title pages titled', author: 'Title Author Pages', page_count: 500});
    assert.deepEqual(parse('Create item type book title "The author of pages" author "Title Author", pages 500').fields,
        {type: 'book', title: 'The author of pages', author: 'Title Author', page_count: 500});
    assert.deepEqual(parse('Create item title "A, B" type book author J.D. Salinger, pages 500').fields,
        {title: 'A, B', type: 'book', author: 'J.D. Salinger', page_count: 500});
    assert.equal(parse('Update item 3, titled The author of books').fields.title, 'The author of books');
    assert.deepEqual(parse('Update item 3, title X author Y').fields, {title: 'X author Y'});
});

test('mixed separators never repair invalid numbers, duplicate aliases or ambiguous unbounded text', () => {
    for (const text of ['Create item type book titled Hobbit title Other author Tolkien, pages 500',
        'Create item type book, title Hobbit, titled Other, author Tolkien, pages 500',
        'Create item type book titled Hobbit author Tolkien, pages -500',
        'Create item type book titled Hobbit author Tolkien, pages 5.5',
        'Create item type book titled Hobbit author Tolkien, pages 5,00',
        'Create item type book titled Hobbit author Tolkien, pages',
        'Create item type book titled Hobbit author Tolkien, unknown 500',
        'Update item 3 pages 500 title The author of books',
        'Update item 3 pages 500 title X author Y',
        'Create item type book title Hobbit, author Tolkien pages 500']) {
        assert.throws(() => parse(text), undefined, text);
    }
});

test("field ordering, comma-separated or comma-free input, numbers and exact text", () => {
    assert.deepEqual(parse("CREATE ITEM author J.D. Salinger pages three hundred ten type BOOK title 1984").fields,
        { author: "J.D. Salinger", page_count: 310, type: "book", title: "1984" });
    assert.deepEqual(parse("Replace item three author Tolkien pages three hundred twenty title The Hobbit Revised").fields,
        { author: "Tolkien", page_count: 320, title: "The Hobbit Revised" });
    assert.deepEqual(parse("Update item two, title Inception Updated, duration one hundred fifty one.").fields,
        { title: "Inception Updated", duration: 151 });
    assert.equal(parse('Update item 3, title "The Author, Volume 2."').fields.title, "The Author, Volume 2.");
    assert.equal(parse('Update item 3 title "Delete item 3"').fields.title, "Delete item 3");
    assert.equal(parse('Update item 3 title "A  B"').fields.title, "A  B");
});

test("positive safe cardinal numbers, decimal and unsafe rejection", () => {
    for (const [text, value] of [["three", 3], ["three hundred ten", 310], ["three hundred and ten", 310],
        ["twenty-one", 21], ["one thousand and one", 1001], ["two million three hundred thousand five", 2300005],
        ["9007199254740991", Number.MAX_SAFE_INTEGER]]) assert.equal(positiveInteger(text), value);
    for (const text of ["", "0", "zero", "-3", "minus three", "negative three", "1.0", "3.5", "three point five",
        "9007199254740992", "one two", "one thousand million", "one hundred and", "one hundred zero", "NaN", "+3", "three and delete item four"]) {
        assert.throws(() => positiveInteger(text), undefined, text);
    }
});

test("missing, duplicate, unknown, ambiguous and multiple commands reject completely", () => {
    for (const text of ["", "Search books", "List books and delete item 3", "Get item", "Get item -3", "Get item 1.5",
        "Create item type book title The Hobbit author Tolkien", "Create item type book title X pages 2",
        "Create item type DVD title X author Y pages 20", "Create item type book title X author Y pages 20, id 5",
        "Create item type book title X author Y pages 20, mystery 3", "Create item type book title X author Y pages 20 pages 21",
        "Create item type book title X author Y pages 20 duration 30", "Replace item 3 title X", "Update item 3",
        "Update item 3 type dvd", "Update item 3 is_available false", "Update item 3 title X title Y",
        "Update item 3 title The Author author Tolkien", "Update item 3 title X and delete item 2",
        "Update item 3 title The author of books", "Update item 3 title X author Y",
        'Update item 3 title "unclosed', 'Update item 3 title "Good" trailing', "Update item 3, title X, publisher Else",
        "Update item 3 duration 10.5", "Update item 3 pages 10,", 'Update item 3 title ""']) {
        assert.throws(() => parse(text), undefined, text);
    }
});

test("comma-bounded Test Book/Test Author equals the quoted command", () => {
    const unquoted = parse("Create item, type book, title Test Book, author Test Author, pages 220");
    const quoted = parse('Create item, type book, title "Test Book", author "Test Author", pages 220');
    assert.deepEqual(unquoted, quoted);
    assert.deepEqual(unquoted.fields, {type: "book", title: "Test Book", author: "Test Author", page_count: 220});
});

test("only comma section prefixes are labels; label words inside values are literal", () => {
    const c = parse("Create item, author Title Author Pages Duration, pages 220, title The author of title pages, type book");
    assert.deepEqual(c.fields, {author: "Title Author Pages Duration", page_count: 220,
        title: "The author of title pages", type: "book"});
    assert.equal(parse("Update item 3, title The author of books").fields.title, "The author of books");
    assert.deepEqual(parse("Update item 3, title X author Y").fields, {title: "X author Y"});
    assert.deepEqual(parse("Update item 3, author Pages Publisher, title Duration Title").fields,
        {author: "Pages Publisher", title: "Duration Title"});
    assert.equal(parse('Update item 3, title "The Author, Volume 2."').fields.title, "The Author, Volume 2.");
});

test("clear comma-free CREATE/PUT/PATCH stay valid while ambiguous optional text fields reject", () => {
    assert.deepEqual(parse("Create item type book title The Hobbit author Tolkien pages three hundred ten").fields,
        {type: "book", title: "The Hobbit", author: "Tolkien", page_count: 310});
    assert.deepEqual(parse("Replace item three title The Hobbit Revised author Tolkien pages 320").fields,
        {title: "The Hobbit Revised", author: "Tolkien", page_count: 320});
    assert.deepEqual(parse("Update item two title Inception Updated duration 151").fields,
        {title: "Inception Updated", duration: 151});
    assert.deepEqual(parse('Update item 3 title "The author of books" author Tolkien').fields,
        {title: "The author of books", author: "Tolkien"});
    for (const text of ["Update item 3 title The author of books", "Update item 3 author Jane title New",
        "Create item type book title Test Book author Test Author pages 220",
        "Create item, type book, title X, author Y, pages 220, pages 221",
        "Create item, type book, title X, author Y, pages 220, mystery 1",
        "Create item, type book, title X, pages 220"]) assert.throws(() => parse(text), undefined, text);
});

test("actual Azure transcript and page/pages/page count aliases yield the same CREATE fields", () => {
    const expected = {type: "book", title: "Hobbit", author: "Tolkien", page_count: 310};
    assert.deepEqual(parse("Create Item Type Book Title Hobbit Author Tolkien. Page 310.").fields, expected);
    for (const alias of ["page", "pages", "page count"]) {
        for (const dot of ["", "."]) {
            assert.deepEqual(parse(`Create Item Type Book Title Hobbit Author Tolkien${dot} ${alias} 310.`).fields, expected);
            assert.deepEqual(parse(`Create item, type book, title Hobbit, author Tolkien, ${alias} 310`).fields, expected);
        }
    }
});

test("boundary dots are structural only before explicit fields; PUT/PATCH and order remain valid", () => {
    assert.deepEqual(parse("Create item. Type book. Page count 310. Author Tolkien. Title Hobbit").fields,
        {type: "book", page_count: 310, author: "Tolkien", title: "Hobbit"});
    for (const alias of ["page", "pages", "page count"]) {
        assert.deepEqual(parse(`Replace item three. Title The Hobbit Revised. Author Tolkien. ${alias} 320.`).fields,
            {title: "The Hobbit Revised", author: "Tolkien", page_count: 320});
        assert.deepEqual(parse(`Update item four. ${alias} three hundred twenty.`).fields, {page_count: 320});
    }
    assert.equal(parse("Update item 3 title Notes on J.D. Salinger").fields.title, "Notes on J.D. Salinger");
    assert.deepEqual(parse("Update item 3 . Title Hobbit. Author Tolkien").fields, {title: "Hobbit", author: "Tolkien"});
    assert.deepEqual(parse("Update item 3 author Tolkien. Title Hobbit").fields, {author: "Tolkien", title: "Hobbit"});
});

test("quoted/comma-separated dotted names and literal page label words are preserved", () => {
    for (const author of ["J.D. Salinger", '"J.D. Salinger"']) {
        assert.equal(parse(`Create item, type book, title Page Count of History, author ${author}, page count 220`).fields.author, "J.D. Salinger");
    }
    assert.equal(parse("Create item Type book Title Hobbit Author J.D. Salinger. Page 310.").fields.author, "J.D. Salinger");
    assert.equal(parse('Create item type book title Hobbit author "J.D. Salinger.". Page 310').fields.author, "J.D. Salinger.");
    assert.equal(parse("Create item type book title Hobbit author J.D. pages 310").fields.author, "J.D.");
    assert.equal(parse('Update item 3, title "Page. Count. Author."').fields.title, "Page. Count. Author.");
});

test("duplicate page aliases, missing fields, ambiguous text and fractional counts still reject", () => {
    for (const text of [
        "Create item type book title Hobbit author Tolkien page 310 pages 320",
        "Create item, type book, title Hobbit, author Tolkien, page 310, page count 320",
        "Create item type book title Hobbit author Tolkien. Page",
        "Create item type book title Hobbit. Page 310",
        "Create item type book title Hobbit author Tolkien. Page 3.5.",
        "Update item 3 title The author of books. Page 310",
        "Create item, type book, title Hobbit, author Tolkien, unknown 310",
    ]) assert.throws(() => parse(text), undefined, text);
});

const book = { id: 3, type: "book", title: "The Hobbit", author: "Tolkien", page_count: 310, is_available: true };

test('real Duration-dot transcript and numeric label/value separators are equivalent', () => {
    const expected = {type: 'dvd', title: 'Inception', author: 'Christopher Nolan', duration: 148};
    assert.deepEqual(parse('Create item type DVD title Inception author Christopher Nolan Duration. 148 minutes.').fields, expected);
    for (const label of ['duration', 'duration in minutes']) for (const separator of [' ', '. ', ': ', ' . ']) {
        for (const prefix of ['Create item type DVD title Inception author Christopher Nolan ',
            'Create item, type DVD, title Inception, author Christopher Nolan, ']) {
            assert.deepEqual(parse(prefix + label + separator + '148 minutes.').fields, expected);
        }
        assert.deepEqual(parse('Replace item 2 title Inception author Christopher Nolan ' + label + separator + 'one hundred and forty eight minutes').fields,
            {title: 'Inception', author: 'Christopher Nolan', duration: 148});
        assert.deepEqual(parse('Update item 2 ' + label + separator + '148 minutes.').fields, {duration: 148});
    }
});

test('all page labels accept a structural dot without changing dotted/quoted text', () => {
    for (const label of ['page', 'pages', 'page count']) for (const separator of [' ', '. ', ': ', ' . ']) {
        for (const [number, value] of [['310', 310], ['three hundred and ten', 310], ['1,310', 1310]]) {
            for (const prefix of ['Create item type book title 1984 author J.D. Salinger ',
                'Create item, type book, title 1984, author J.D. Salinger, ']) {
                assert.deepEqual(parse(prefix + label + separator + number).fields,
                    {type: 'book', title: '1984', author: 'J.D. Salinger', page_count: value});
            }
            assert.deepEqual(parse('Update item three ' + label + separator + number).fields, {page_count: value});
        }
    }
    assert.equal(parse('Create item, type book, title "Duration. Pages. 1984.", author "J.D. Salinger.", pages. 310').fields.author, 'J.D. Salinger.');
    assert.deepEqual(parse('Update item 3, title Duration. Study, author J.D. Salinger').fields,
        {title: 'Duration. Study', author: 'J.D. Salinger'});
});

test('numeric label punctuation never repairs missing/invalid numbers or ambiguous fields', () => {
    for (const tail of ['duration.', 'duration. -148', 'duration. 1.5 minutes', 'duration. 0 minutes',
        'duration. bananas minutes', 'duration. "148"', 'duration.. 148', 'duration. . 148',
        'duration in minutes. one two minutes', 'duration. 148 minutes duration 149',
        'pages. -310', 'pages. 1,00', 'page count. 3.5', 'page count. author Tolkien']) {
        assert.throws(() => parse('Update item 2 ' + tail), undefined, tail);
    }
    assert.throws(() => parse('Update item 3 title The author of books pages. 310'));
});

test("both exact manually reported CREATE inputs produce the expected fields", () => {
    assert.deepEqual(parse('Create item; type: book; title: Test Book; author: Test Author; pages: three hundred and ten.').fields,
        {type: 'book', title: 'Test Book', author: 'Test Author', page_count: 310});
    assert.deepEqual(parse('Create item, type DVD, title Inception, author Christopher Nolan, duration in minutes 148.').fields,
        {type: 'dvd', title: 'Inception', author: 'Christopher Nolan', duration: 148});
    assert.equal(positiveInteger('three hundred and ten'), 310);
    for (const text of ['pages three hundred and ten', 'in minutes 148', '148 minutes']) {
        assert.throws(() => positiveInteger(text)); // Labels/units must be consumed by field parsing.
    }
});

test("multiword labels require exact unquoted word boundaries", () => {
    for (const text of ['duration "in" "minutes" 148', 'duration in "minutes" 148',
        'duration in minutesExtra 148', 'duration inminutes 148', 'duration in minutes',
        'duration in minutes 148 duration 149', 'page "count" 310', 'page counter 310']) {
        assert.throws(() => parse('Update item 2 ' + text), undefined, text);
    }
    assert.equal(parse('Update item 2 DURATION\n IN\t MINUTES: 148 minutes').fields.duration, 148);
});

test("case, syntax whitespace and line breaks preserve text values", () => {
    assert.deepEqual(parse(' \n CrEaTe\t ITEM\n TYPE\t BoOk\n TITLE 1984\n AUTHOR J.D. Salinger\n PAGE\n COUNT three\n hundred\t and ten! ').fields,
        {type: "book", title: "1984", author: "J.D. Salinger", page_count: 310});
    assert.equal(parse('Get item three\n hundred\t and ten').id, 310);
    assert.equal(parse('LIST\n CHECKED\t OUT\n DVDs').filters.available, false);
    assert.equal(parse('Update item 3; title: "A  B\\nC"').fields.title, 'A  B\nC');
});

test("explicit comma, period, semicolon and colon boundaries and label colons", () => {
    for (const separator of [", ", ". ", "; ", ": "]) {
        const text = ['Create item', 'type: book', 'title: 1984', 'author: J.D. Salinger', 'pages: 310'].join(separator);
        assert.deepEqual(parse(text).fields, {type: "book", title: "1984", author: "J.D. Salinger", page_count: 310}, text);
        assert.deepEqual(parse(['Update item 3', 'title: Hobbit', 'author: Tolkien'].join(separator)).fields,
            {title: "Hobbit", author: "Tolkien"});
    }
    assert.deepEqual(parse('Replace item 3; author: Tolkien, pages: 320; title: Revised').fields,
        {author: "Tolkien", page_count: 320, title: "Revised"});
    assert.equal(parse('Update item 3; title: The author of pages').fields.title, 'The author of pages');
    assert.equal(parse('Update item 3; title: "1984: Notes; J.D., Volume 1."').fields.title, '1984: Notes; J.D., Volume 1.');
});

test("terminal punctuation sequences are syntax outside quoted text", () => {
    for (const ending of ['.', '!', '?', ';', ':', '?!', '...']) {
        assert.equal(parse('List items' + ending).action, 'list');
        assert.equal(parse('Get item three' + ending).id, 3);
        assert.equal(parse('Update item 3 pages 310' + ending).fields.page_count, 310);
        assert.equal(parse('Update item 3 title "Why?!"' + ending).fields.title, 'Why?!');
    }
    assert.throws(() => parse('Update item 3 pages 310,'));
});

test("strict thousands groups normalize only numeric fields", () => {
    for (const [text, value] of [['1,000', 1000], ['12,345', 12345], ['1,234,567', 1234567], ['9,007,199,254,740,991', Number.MAX_SAFE_INTEGER]]) {
        assert.equal(positiveInteger(text), value);
        assert.equal(parse('Get item ' + text).id, value);
        assert.equal(parse('Update item 3 pages ' + text).fields.page_count, value);
        assert.equal(parse('Update item 3; duration: ' + text + ' minutes').fields.duration, value);
    }
    assert.equal(parse('Create item, type book, title 1,984, author J.D. Salinger, pages 1,310').fields.title, '1,984');
    for (const text of ['1,00', '12,34,567', '1234,567', '1,,000', '1, 000', '0,001', '1,000.5', '9,007,199,254,740,992']) {
        assert.throws(() => positiveInteger(text), undefined, text);
        assert.throws(() => parse('Update item 3 pages ' + text), undefined, text);
    }
});

test("duration label aliases and optional minute units keep integer validation", () => {
    for (const label of ['duration', 'duration in minutes']) for (const unit of ['', ' minute', ' minutes']) {
        assert.equal(parse(`Update item two ${label} one hundred and forty eight${unit}.`).fields.duration, 148);
        assert.equal(parse(`Create item; type: DVD; title: Film; author: Director; ${label}: 148${unit}`).fields.duration, 148);
        assert.equal(parse(`Replace item 2 title Film author Nolan ${label} 150${unit}`).fields.duration, 150);
    }
    for (const text of ['duration in minute 148', 'duration 148 seconds', 'duration 1.5 minutes', 'duration minutes',
        'pages 310 minutes', 'duration 10 minute minutes', 'duration 10; duration in minutes 20']) {
        assert.throws(() => parse('Update item 2 ' + text), undefined, text);
    }
});

test("ambiguous or unknown sections stay errors despite tolerant separators", () => {
    for (const text of ['Update item 3 title The author of books', 'Update item 3 title X author Y',
        'Update item 3; title: X; mystery: 4', 'Update item 3: title: X: publisher: Y',
        'Create item; type book; title X; pages 10', 'Update item 3; title: X; title: Y',
        'Update item 3; title: Notes: Something', 'Update item 3; pages: 10; delete item 2']) {
        assert.throws(() => parse(text), undefined, text);
    }
});

function adapter(replies) {
    const requests = [];
    return { requests, apiRequest: async (path, options = {}) => {
        requests.push({ path, ...options }); const result = replies.shift();
        assert.notEqual(result, undefined, "Unexpected request"); if (result instanceof Error) throw result; return result;
    }, refreshItems: async () => [], setFilters() {} };
}

test("PUT/PATCH preflight uses fresh item type and forbids a mismatched write", async () => {
    let a = adapter([book, { ...book, title: "Revised", page_count: 320 }]);
    let result = await execute(parse("Replace item 3 title Revised author Tolkien pages 320"), a);
    assert.equal(result.ok, true); assert.equal(a.requests[0].path, "/api/items/3"); assert.equal(a.requests[1].method, "PUT");
    assert.deepEqual(JSON.parse(a.requests[1].body), { title: "Revised", author: "Tolkien", page_count: 320 });
    a = adapter([{ ...book, type: "dvd", duration: 148 }]);
    result = await execute(parse("Update item 3 pages 330"), a);
    assert.equal(result.ok, false); assert.equal(a.requests.length, 1); assert.match(result.responseText, /dvd/);
});

test("mutation success plus refresh failure remains success and is not replayed", async () => {
    const a = adapter([{ ...book, id: 4 }]); a.refreshItems = async () => { throw new Error("offline"); };
    const result = await execute(parse("Create item type book title The Hobbit author Tolkien pages 310"), a);
    assert.equal(result.ok, true); assert.match(result.responseText, /Successfully created book.*ID 4/);
    assert.match(result.warning, /operation succeeded/); assert.equal(a.requests.length, 1);
});

test("DELETE 204, model checkout message, 404, 409 and uncertain outcomes", async () => {
    let a = adapter([null]); let result = await execute(parse("Delete item 3"), a);
    assert.equal(result.responseText, "Successfully deleted item 3."); assert.equal(a.requests[0].method, "DELETE");
    a = adapter([{ item: { ...book, type: "dvd", is_available: false }, message: "Successful checkout. Handle with care: Do not scratch the disc." }]);
    result = await execute(parse("Check out item 3"), a); assert.match(result.responseText, /Handle with care/);
    for (const status of [400, 404, 409]) {
        a = adapter([Object.assign(new Error("State or input error"), { status })]);
        result = await execute(parse("Get item 3"), a); assert.equal(result.ok, false);
        assert.match(result.responseText, status === 404 ? /item 3 was not found/ : new RegExp("HTTP " + status));
    }
    a = adapter([Object.assign(new Error("offline"), { uncertain: true })]);
    result = await execute(parse("Delete item 3"), a); assert.match(result.responseText, /may have been applied/); assert.equal(a.requests.length, 1);
});

test("empty and long summaries are bounded and use actual IDs and titles", () => {
    assert.equal(summarizeItems([]), "No items match these filters.");
    const items = Array.from({ length: 110 }, (_, i) => ({ id: i + 10, title: "x".repeat(1000) }));
    const text = summarizeItems(items); assert.match(text, /110 items found/); assert.match(text, /10:/);
    assert.doesNotMatch(text, /15:/); assert.match(text, /first 100 cards/); assert.ok(text.length < 600);
});
