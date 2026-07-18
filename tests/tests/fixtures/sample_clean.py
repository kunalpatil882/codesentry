"""A tiny, deliberately clean module used to test for false positives."""


def add(a, b):
    """Return the sum of two numbers."""
    return a + b


def divide(a, b):
    """Return a divided by b, raising ValueError on division by zero."""
    if b == 0:
        raise ValueError("cannot divide by zero")
    return a / b
