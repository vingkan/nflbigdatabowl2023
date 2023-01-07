from typing import Type

import ipywidgets as widgets


def unsnake(raw: str) -> str:
    """Converts a snake-case string to upper sentence case."""
    cleaned = raw.lower()
    words = []
    for word in cleaned.split("_"):
        letters = list(word)
        letters[0] = letters[0].upper()
        word = "".join(letters)
        words.append(word)
    return " ".join(words)


def make_dropdown(options, name) -> Type[widgets.Dropdown]:
    """Creates a new dropdown from the given options."""
    return widgets.Dropdown(options=options, value=options[0], description=name)
