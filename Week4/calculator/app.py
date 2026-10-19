"""Flask interface for the existing Calculator class."""

import math

from flask import Flask, jsonify, render_template, request

from custom_classes import Calculator


app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/calculate")
def calculate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Geçerli bir JSON nesnesi gönderin."), 400

    if not all(field in data for field in ("operation", "x", "y")):
        return jsonify(error="operation, x ve y alanları zorunludur."), 400

    calculator = Calculator()
    operations = {
        "add": calculator.add,
        "subtract": calculator.subtract,
        "multiply": calculator.multiply,
        "divide": calculator.divide,
    }
    operation = data["operation"]
    if not isinstance(operation, str) or operation not in operations:
        return jsonify(error="Geçersiz işlem. add, subtract, multiply veya divide kullanın."), 400

    x, y = data["x"], data["y"]
    for value in (x, y):
        if type(value) not in (int, float):
            return jsonify(error="x ve y sayı olmalıdır; boolean kabul edilmez."), 400
        if isinstance(value, float) and not math.isfinite(value):
            return jsonify(error="x ve y sonlu sayılar olmalıdır."), 400

    try:
        result = operations[operation](x, y)
    except ValueError:
        return jsonify(error="Sıfıra bölme yapılamaz."), 400
    except OverflowError:
        return jsonify(error="Sayılar hesaplanabilir aralığın dışında."), 400

    if isinstance(result, float) and not math.isfinite(result):
        return jsonify(error="Sonuç sonlu bir sayı olmalıdır."), 400
    return jsonify(result=result), 200


if __name__ == "__main__":
    app.run()
