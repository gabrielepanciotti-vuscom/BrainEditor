"""Read side of an area: its notes and the open questions of the internal register.

The register (OPEN_QUESTIONS_NOTE) is a markdown
note with one table per role; each row has an id like `SC-01`, whose prefix tells the
area. A question is closed when its text is struck through or says "chiusa il ...":
those rows stay in the register as history but are not shown as open.
"""

import re
from pathlib import Path

from pydantic import BaseModel

from .validatori import FILE_GESTITI, INDICI, frontmatter, wikilink


class VoceNota(BaseModel):
    # Path relative to brain/, what the editor opens.
    nota: str
    titolo: str
    stato: str | None
    aggiornata: str | None


class Domanda(BaseModel):
    id: str
    domanda: str
    perche: str
    # Notes the question touches: wikilink name, and path when it resolves.
    note: list[str]
    percorsi: dict[str, str]


_ID = re.compile(r"^[A-Z]{2,}-\d+$")
_CHIUSA = re.compile(r"~~|\bchius[ao]\s+il\b", re.IGNORECASE)


def elenca_note(brain_root: Path, cartelle: list[str]) -> list[VoceNota]:
    """Notes under the given brain folders (recursive), hubs and managed files excluded."""
    out: list[VoceNota] = []
    visti: set[str] = set()
    for cartella in cartelle:
        base = brain_root / cartella
        if not base.is_dir():
            continue
        for md in sorted(base.rglob("*.md")):
            rel = md.relative_to(brain_root).as_posix()
            if md.name in FILE_GESTITI or md.stem in INDICI or rel in visti:
                continue
            visti.add(rel)
            fm = frontmatter(md.read_text(encoding="utf-8")) or {}
            out.append(
                VoceNota(
                    nota=rel,
                    titolo=fm.get("title") or md.stem,
                    stato=fm.get("status") or None,
                    aggiornata=fm.get("updated") or None,
                )
            )
    return out


def _celle(riga: str) -> list[str]:
    # The register writes wikilinks without `|` aliases, so bare pipes split the cells.
    return [c.strip() for c in riga.strip().strip("|").split("|")]


def domande_aperte(testo: str, prefissi: list[str]) -> list[Domanda]:
    """Open rows of the register whose id starts with one of the prefixes."""
    out: list[Domanda] = []
    for riga in testo.splitlines():
        if not riga.lstrip().startswith("|"):
            continue
        celle = _celle(riga)
        if len(celle) < 2 or not _ID.match(celle[0]):
            continue
        if celle[0].split("-")[0] not in prefissi or _CHIUSA.search(celle[1]):
            continue
        out.append(
            Domanda(
                id=celle[0],
                domanda=celle[1],
                note=wikilink(celle[2]) if len(celle) > 2 else [],
                perche=celle[3] if len(celle) > 3 else "",
                percorsi={},
            )
        )
    return out


def risolvi_percorsi(brain_root: Path, domande: list[Domanda]) -> list[Domanda]:
    """Fill each question's wikilink -> path map, so the editor can open the note."""
    nomi = {n for d in domande for n in d.note}
    if not nomi:
        return domande
    trovati: dict[str, str] = {}
    for md in brain_root.rglob("*.md"):
        if md.stem in nomi and md.stem not in trovati and "sources" not in md.parts:
            trovati[md.stem] = md.relative_to(brain_root).as_posix()
    for d in domande:
        d.percorsi = {n: trovati[n] for n in d.note if n in trovati}
    return domande
