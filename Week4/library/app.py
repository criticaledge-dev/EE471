"""HTTP/JSON adapter for the in-memory library models."""

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from custom_classes import Book, DVD, ItemNotFoundError, ItemStateError, LibraryCollection


app = Flask(__name__)
collection = LibraryCollection()
collection.add_item(Book("The Hobbit", "J.R.R. Tolkien", 310))
collection.add_item(DVD("Inception", "Christopher Nolan", 148))
collection.add_item(Book("1984", "George Orwell", 328))


def _json_object():
    """Decode a JSON object and normalize invalid bodies to ValueError."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a valid JSON object with JSON Content-Type.")
    return data


@app.errorhandler(ItemNotFoundError)
def item_not_found(error):
    """Translate a missing model item into HTTP 404."""
    return jsonify(error=str(error)), 404


@app.errorhandler(ItemStateError)
def item_state_error(error):
    """Translate an invalid state transition into HTTP 409."""
    return jsonify(error=str(error)), 409


@app.errorhandler(ValueError)
def invalid_input(error):
    """Translate model or request validation failures into HTTP 400."""
    return jsonify(error=str(error)), 400


@app.errorhandler(HTTPException)
def http_error(error):
    """Return JSON for routing and other HTTP errors, preserving headers."""
    response = error.get_response()
    response.data = app.json.dumps({"error": error.description})
    response.content_type = "application/json"
    return response


@app.post("/api/items")
def create_item():
    """Create a model item from its JSON description."""
    item = collection.create_item(_json_object())
    return jsonify(item.to_dict()), 201


@app.get("/api/items")
def list_items():
    """Decode optional query filters and serialize matching items."""
    available = None
    if "available" in request.args:
        values = {"true": True, "false": False}
        value = request.args["available"]
        if value not in values:
            raise ValueError("available must be 'true' or 'false'.")
        available = values[value]
    items = collection.list_items(available=available, item_type=request.args.get("type"))
    return jsonify([item.to_dict() for item in items]), 200


@app.get("/api/items/<int:item_id>")
def get_item(item_id):
    """Serialize the requested item."""
    return jsonify(collection.get_item(item_id).to_dict()), 200


@app.put("/api/items/<int:item_id>")
def replace_item(item_id):
    """Pass a complete editable representation to the model."""
    item = collection.replace_item(item_id, _json_object())
    return jsonify(item.to_dict()), 200


@app.patch("/api/items/<int:item_id>")
def patch_item(item_id):
    """Pass a partial editable representation to the model."""
    item = collection.patch_item(item_id, _json_object())
    return jsonify(item.to_dict()), 200


@app.delete("/api/items/<int:item_id>")
def delete_item(item_id):
    """Remove an item and return an entirely empty success response."""
    collection.remove_item(item_id)
    return "", 204


@app.post("/api/items/<int:item_id>/checkout")
def checkout_item(item_id):
    """Return the checkout message supplied by the model with its new state."""
    item = collection.get_item(item_id)
    message = item.checkout()
    return jsonify(message=message, item=item.to_dict()), 200


@app.post("/api/items/<int:item_id>/return")
def return_item(item_id):
    """Return the model's return message and updated item state."""
    item = collection.get_item(item_id)
    message = item.return_item()
    return jsonify(message=message, item=item.to_dict()), 200


if __name__ == "__main__":
    app.run()
