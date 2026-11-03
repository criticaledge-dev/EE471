"use strict";

const display = document.querySelector("#display");
const error = document.querySelector("#error");
const buttons = document.querySelectorAll("[data-digit], [data-operation], [data-action]");
const symbols = { add: "+", subtract: "−", multiply: "×", divide: "÷" };
let entry = "0";
let firstOperand = null;
let operation = null;
let waitingForOperand = false;
let busy = false;
let voiceBusy = false;

function render() {
    display.textContent = operation
        ? `${firstOperand} ${symbols[operation]}${waitingForOperand ? "" : ` ${entry}`}`
        : entry;
    display.setAttribute("aria-busy", String(busy));
    display.scrollLeft = display.scrollWidth;
    document.querySelectorAll("[data-operation]").forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.operation === operation));
    });
    buttons.forEach((button) => { button.disabled = busy || voiceBusy; });
    document.querySelector("#voice-start").disabled = busy || voiceBusy;
}

function clearError() {
    error.textContent = "";
    error.hidden = true;
}

function enterDigit(digit) {
    clearError();
    if (waitingForOperand) {
        entry = "0";
        waitingForOperand = false;
    }
    if (digit === ".") {
        if (!entry.includes(".") && !entry.includes("e")) entry += ".";
    } else {
        entry = entry === "0" ? digit : entry + digit;
    }
    render();
}

async function calculate() {
    if (!operation || waitingForOperand) return true;
    clearError();
    busy = true;
    render();
    try {
        const x = Number(firstOperand);
        const y = Number(entry);
        if (!Number.isFinite(x) || !Number.isFinite(y)) {
            throw new Error("Lütfen sonlu sayılar girin.");
        }
        const response = await fetch("/api/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ operation, x, y }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "İşlem tamamlanamadı.");
        if (typeof data.result !== "number" || !Number.isFinite(data.result)) {
            throw new Error("Sonuç tarayıcıda gösterilebilecek aralığın dışında.");
        }
        entry = String(data.result);
        firstOperand = null;
        operation = null;
        waitingForOperand = true;
        return true;
    } catch (failure) {
        error.textContent = failure instanceof TypeError
            ? "Sunucuya ulaşılamadı. Bağlantınızı kontrol edip tekrar deneyin."
            : failure.message;
        error.hidden = false;
        return false;
    } finally {
        busy = false;
        render();
    }
}

async function chooseOperation(nextOperation) {
    if (operation && !waitingForOperand && !(await calculate())) return;
    clearError();
    firstOperand = entry;
    operation = nextOperation;
    waitingForOperand = true;
    render();
}

function clear() {
    window.calculatorAudio?.cancel();
    entry = "0";
    firstOperand = null;
    operation = null;
    waitingForOperand = false;
    clearError();
    render();
}

buttons.forEach((button) => {
    button.addEventListener("click", () => {
        if (busy || voiceBusy) return;
        if (button.dataset.digit !== undefined) {
            enterDigit(button.dataset.digit);
            window.calculatorAudio?.key(button.dataset.digit);
        }
        else if (button.dataset.operation) {
            window.calculatorAudio?.key(button.dataset.operation);
            void chooseOperation(button.dataset.operation);
        }
        else if (button.dataset.action === "equals") {
            const hasCalculation = operation && !waitingForOperand;
            const audio = window.calculatorAudio;
            const ticket = audio?.ticket();
            void calculate().then(success => {
                if (success && hasCalculation) audio?.result(entry, ticket);
            });
        }
        else if (button.dataset.action === "clear") clear();
    });
});

document.addEventListener("keydown", (event) => {
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    const operationKeys = { "+": "add", "-": "subtract", "*": "multiply", "/": "divide" };
    const supported = /^[0-9.,]$/.test(event.key) || operationKeys[event.key]
        || ["Enter", "=", "Escape", "Backspace"].includes(event.key);
    if (!supported) return;
    event.preventDefault();
    if (busy || voiceBusy) return;
    if (/^[0-9.,]$/.test(event.key)) enterDigit(event.key === "," ? "." : event.key);
    else if (operationKeys[event.key]) void chooseOperation(operationKeys[event.key]);
    else if (event.key === "Enter" || event.key === "=") void calculate();
    else if (event.key === "Escape") clear();
    else if (event.key === "Backspace" && !waitingForOperand) {
        entry = entry.slice(0, -1);
        if (!entry || entry === "-") entry = "0";
        clearError();
        render();
    }
});

// Voice commands use exactly the same input/operation/API flow as the keypad.
window.calculatorVoice = {
    setBusy(value) {
        window.calculatorAudio?.setMicrophoneBusy(value);
        voiceBusy = value;
        render();
    },
    async apply(command) {
        clear();
        for (const digit of command.left) enterDigit(digit);
        await chooseOperation(command.operation);
        for (const digit of command.right) enterDigit(digit);
        const success = await calculate(); // "is": preserve the existing API/error flow.
        // entry contains the validated successful API response; do not recalculate.
        return success ? { result: entry } : null;
    },
};
render();
