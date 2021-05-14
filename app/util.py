"""Utilities."""
import json
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent / "openapi_examples"


def load_example(name):
    """Load example from JSON file."""
    with open(EXAMPLES_DIR / (name + ".json"), "r") as stream:
        return json.load(stream)


def drop_nulls(obj):
    """Recursively remove null-valued properties."""
    if isinstance(obj, list):
        return [
            drop_nulls(el) for el in obj
        ]
    if isinstance(obj, dict):
        return {
            key: drop_nulls(value)
            for key, value in obj.items()
            if value is not None
        }
    return obj
