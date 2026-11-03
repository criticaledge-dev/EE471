// API orchestration only. Library rules and the sole collection stay on the server.
export const LIST_CARD_LIMIT = 100;
export const SUMMARY_ITEM_LIMIT = 5;
const short = value => String(value).length <= 60 ? String(value) : String(value).slice(0, 59) + "…";
const named = item => `Item ${item.id}, '${short(item.title)}'`;

export function summarizeItems(items) {
    if (!items.length) return "No items match these filters.";
    const sample = items.slice(0, SUMMARY_ITEM_LIMIT).map(item => `${item.id}: '${short(item.title)}'`).join("; ");
    return `${items.length} item${items.length === 1 ? "" : "s"} found. ${sample}.`
        + (items.length > SUMMARY_ITEM_LIMIT ? ` First ${SUMMARY_ITEM_LIMIT} items summarized.` : "")
        + (items.length > LIST_CARD_LIMIT ? ` Showing the first ${LIST_CARD_LIMIT} cards.` : "");
}

export function commandErrorText(error, command) {
    if (error.uncertain) return "Sorry, the server response could not be confirmed. The operation may have been applied. Check the collection before trying again; it was not automatically retried.";
    if (error.status === 404 && command?.id !== null && command?.id !== undefined) return `Sorry, item ${command.id} was not found.`;
    return `Sorry, ${error.status ? "HTTP " + error.status + ": " : ""}${error.message}`;
}

export async function executeLibraryCommand(command, { apiRequest, refreshItems, setFilters, onMutation = () => {}, signal }) {
    const result = { ok: false, command, request: null, data: null, responseText: "", warning: "", uncertain: false };
    try {
        const ensureActive = () => { if (signal?.aborted) throw new Error("Command canceled before sending the next request."); };
        ensureActive();
        const path = command.id === null ? "/api/items" : `/api/items/${command.id}`;
        if (command.action === "list") {
            setFilters(command.filters);
            const query = new URLSearchParams();
            if (command.filters.type) query.set("type", command.filters.type);
            if (command.filters.available !== null) query.set("available", String(command.filters.available));
            result.request = { method: "GET", path: "/api/items" + (query.size ? "?" + query : "") };
            result.data = await refreshItems({ limit: LIST_CARD_LIMIT });
            result.responseText = summarizeItems(result.data);
        } else if (command.action === "get") {
            result.request = { method: "GET", path };
            const item = result.data = await apiRequest(path);
            result.responseText = `${named(item)} is a ${item.type}, by ${short(item.author)}, `
                + (item.type === "book" ? `${item.page_count} pages` : `${item.duration} minutes`)
                + `, ${item.is_available ? "available" : "checked out"}.`;
        } else {
            if (["replace", "update"].includes(command.action)) {
                const current = await apiRequest(path); // Fresh type; never trust an old rendered card.
                if (!["book", "dvd"].includes(current.type)) throw new Error("The server returned an unsupported item type.");
                const detail = current.type === "book" ? "page_count" : "duration";
                if (Object.keys(command.fields).some(key => !["title", "author", detail].includes(key))) {
                    throw new Error(`Item ${command.id} is a ${current.type}; use ${detail === "page_count" ? "pages" : "duration"} for this item.`);
                }
            }
            const method = ({ create: "POST", replace: "PUT", update: "PATCH", delete: "DELETE", checkout: "POST", return: "POST" })[command.action];
            if (!method) throw new Error("Unsupported command action.");
            const url = path + (["checkout", "return"].includes(command.action) ? "/" + command.action : "");
            const options = { method };
            if (["create", "replace", "update"].includes(command.action)) {
                options.headers = { "Content-Type": "application/json" };
                options.body = JSON.stringify(command.fields);
            }
            result.request = { method, path: url, ...(options.body ? { body: command.fields } : {}) };
            ensureActive(); // Cancellation during the type lookup must not issue a later write.
            const data = result.data = await apiRequest(url, options); // Exactly one mutation request.
            if (command.action === "create") result.responseText = `Successfully created ${data.type} '${short(data.title)}' with ID ${data.id}.`;
            else if (command.action === "delete") result.responseText = `Successfully deleted item ${command.id}.`;
            else if (["replace", "update"].includes(command.action)) result.responseText = `Successfully ${command.action === "replace" ? "replaced" : "updated"} item ${data.id}, '${short(data.title)}'.`;
            else result.responseText = `${named(data.item)} has been ${command.action === "checkout" ? "checked out" : "returned"}. ${data.message}`;
            result.ok = true; // The mutation succeeded even if the following view refresh fails.
            onMutation(command, data);
            try { await refreshItems(); }
            catch { result.warning = "The operation succeeded, but the list could not be refreshed. Use Refresh list; do not repeat the operation."; }
        }
        result.ok = true;
    } catch (error) {
        // Only a view refresh is caught after mutation success; never replay a write.
        result.responseText = commandErrorText(error, command);
        result.uncertain = Boolean(error.uncertain);
        result.status = error.status || null;
    }
    return result;
}
