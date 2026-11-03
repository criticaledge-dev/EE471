const digits = Object.fromEntries(
    "zero one two three four five six seven eight nine".split(" ").map((word, i) => [word, String(i)]),
);
const operations = { plus: "add", minus: "subtract", times: "multiply", over: "divide" };
const symbols = { plus: "+", minus: "−", times: "×", over: "÷" };
const symbolWords = { "+": "plus", "-": "minus", "−": "minus", "*": "times", "×": "times", "/": "over", "÷": "over", "=": "is" };

export function parseVoiceCommand(text) {
    if (typeof text !== "string" || !text.trim() || text.length > 2000) {
        throw new Error("Tanınan komut boş veya çok uzun.");
    }
    // Keep dots before digits, including malformed numbers, so validation rejects
    // .5 or 1..5 rather than silently changing their value. Strip sentence dots.
    const normalized = text.toLowerCase().replace(/[.,!?;:"“”‘’()]/g, (char, index) =>
        char === "." && /\d/.test(text[index + 1] || " ")
            ? "." : " ");
    // Isolate only explicit operator symbols; never remove unknown tokens.
    const tokens = normalized.replace(/([+\-−*×/÷=])/g, " $1 ").trim().split(/\s+/)
        .map(token => Object.hasOwn(symbolWords, token) ? symbolWords[token] : token);
    const unsupported = tokens.some(token => !Object.hasOwn(digits, token) && !Object.hasOwn(operations, token)
        && token !== "point" && token !== "is" && !/^\d+(?:\.\d+)?$/.test(token));
    if (unsupported) throw new Error("Desteklenmeyen kelime var. Yalnızca sayı kelimeleri, point, plus, minus, times, over ve is kullanın.");
    if (tokens.at(-1) !== "is" || tokens.filter(token => token === "is").length !== 1) {
        throw new Error("Komut tek bir is (eşittir) ile bitmelidir.");
    }
    const indexes = tokens.flatMap((token, i) => Object.hasOwn(operations, token) ? [i] : []);
    if (indexes.length !== 1) throw new Error("İki sayı arasında tek bir işlem söyleyin; örnek: five plus two is.");
    const at = indexes[0];
    function number(parts) {
        if (parts.length > 1 && parts.some(token => /^\d+\.\d+$/.test(token))) {
            throw new Error("Ondalık rakamın yanına ek sayı koymayın.");
        }
        const value = parts.map(token => Object.hasOwn(digits, token) ? digits[token] : token === "point" ? "." : token).join("");
        if (!/^\d+(?:\.\d+)?$/.test(value) || !Number.isFinite(Number(value))) {
            throw new Error("Geçersiz sayı dizisi. Ondalık için one point five gibi bir sayı söyleyin.");
        }
        return value.replace(/^0+(?=\d)/, "");
    }
    const left = number(tokens.slice(0, at));
    const right = number(tokens.slice(at + 1, -1));
    return { left, right, operation: operations[tokens[at]], normalized: `${left} ${symbols[tokens[at]]} ${right} =` };
}
