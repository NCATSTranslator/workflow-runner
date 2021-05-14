"""Utilities."""
import json
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent / "openapi_examples"


def load_example(name):
    """Load example from JSON file."""
    with open(EXAMPLES_DIR / (name + ".json"), "r") as stream:
        return json.load(stream)
