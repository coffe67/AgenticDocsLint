from __future__ import annotations

from slideforge.models import Deck, Slide


def normalize_deck(deck: Deck) -> Deck:
    for s in deck.slides:
        s.title = (s.title or "").strip()
        s.bullets = [b.strip() for b in s.bullets if b and b.strip()]
        if s.notes:
            s.notes = s.notes.strip()
    return deck

