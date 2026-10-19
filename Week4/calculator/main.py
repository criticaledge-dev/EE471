from custom_classes import Calculator


calculator = Calculator()

result = calculator.add(10, 5)
result = calculator.multiply(result, 2)
result = calculator.divide(result, 3)

print(result)