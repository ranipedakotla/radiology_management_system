LIMITS = {
    "H1": 10,
    "X": 5
}

def validate_quantity(category: str, quantity: int):
    if category in LIMITS and quantity > LIMITS[category]:
        raise ValueError("Quantity exceeds statutory limit")
