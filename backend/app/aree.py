"""Areas and owners of the questionnaire: data, not code (AREAS_FILE or the tree)."""

import json
from typing import Any

from pydantic import BaseModel, Field

from .config import settings


class Area(BaseModel):
    id: str
    nome: str
    descrizione: str = ""
    # Brain folders (relative to brain/) this area writes into.
    cartelle_brain: list[str] = Field(default_factory=list)
    # Owners come from the questionnaire answers; empty until someone answers.
    responsabili: list[str] = Field(default_factory=list)
    # Id prefixes of this area's rows in the open-questions register (e.g. "SC").
    prefissi_domande: list[str] = Field(default_factory=list)


def carica_aree() -> list[Area]:
    """All areas, in questionnaire order."""
    raw: dict[str, Any] = json.loads(settings.areas_file.read_text(encoding="utf-8"))
    return [Area(**a) for a in raw["aree"]]


def trova_area(area_id: str) -> Area | None:
    return next((a for a in carica_aree() if a.id == area_id), None)
