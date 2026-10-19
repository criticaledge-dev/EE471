"use strict";

const display = document.querySelector("#display");
const error = document.querySelector("#error");
const buttons = document.querySelectorAll("button");
const symbols = { add: "+", subtract: "−", multiply: "×", divide: "÷" };
let entry = "0";
let firstOperand = null;
let operation = null;
let waitingForOperand = false;
let busy = false;

function render() {
    display.textContent = operation
        ? `${firstOperand} ${symbols[operation]}${waitingForOperand ? "" : ` ${entry}`}`
        : entry;
    display.setAttribute("aria-busy", String(busy));
    display.scrollLeft = display.scrollWidth;
    document.querySelectorAll("[data-operation]").forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.operation === operation));
    });
    buttons.forEach((button) => { button.disabled = busy; });
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
    entry = "0";
    firstOperand = null;
    operation = null;
    waitingForOperand = false;
    clearError();
    render();
}

buttons.forEach((button) => {
    button.addEventListener("click", () => {
        if (busy) return;
        if (button.dataset.digit !== undefined) enterDigit(button.dataset.digit);
        else if (button.dataset.operation) void chooseOperation(button.dataset.operation);
        else if (button.dataset.action === "equals") void calculate();
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
    if (busy) return;
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

render();
