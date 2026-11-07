"""Form rules of a brain note, checked before every commit.

Same rules as the Life brain gate (suite_core.nodes.brain_gate), restated here because
BrainEditor runs without suite_core: complete frontmatter, at least 3 outgoing wikilinks
to existing notes, no broken link, body of at most 300 lines, and `classification`
inherited from the folder (a note may omit it or tighten it, never loosen it).
"""

import re
from pathlib import Path, PurePosixPath

from pydantic import BaseModel

CAMPI_OBBLIGATORI = ("title", "summary", "tags", "status", "created", "updated")
MIN_WIKILINK = 3
MAX_RIGHE = 300

# Raw material and working lists, not knowledge: out of the corpus (same as the gate).
CARTELLE_ESCLUSE = {"sources", "workspace"}
FILE_GESTITI = {"index.md", "README.md", "CHANGELOG.md", "_README.md", "showcase.md"}
# Linkable but not a note: a link to it is not broken, it does not count among the 3.
PUNTI_INGRESSO = {"README"}
INDICI = {"_index", "index"}
# Least to most restricted; "interno" is the Italian spelling some notes carry.
LIVELLI = {"public": 0, "internal": 1, "interno": 1, "confidential": 2, "restricted": 3}

_FM = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
_CHIAVE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")
_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
# `[[X]]` inside code is a literal, not a link.
_CODICE = re.compile(r"```.*?```|~~~.*?~~~|(`+)[^`\n]*?\1", re.DOTALL)


class Problema(BaseModel):
    regola: str
    messaggio: str


class Esito(BaseModel):
    valida: bool
    problemi: list[Problema]
    wikilink_validi: int
    righe_corpo: int
    classification: str | None


def frontmatter(testo: str) -> dict[str, str] | None:
    """Top-level `key: value` pairs of the leading YAML block, None if there is none."""
    m = _FM.match(testo)
    if not m:
        return None
    out: dict[str, str] = {}
    for riga in m.group(1).splitlines():
        km = _CHIAVE.match(riga)
        if km and not riga.lstrip().startswith("#"):
            out[km.group(1)] = km.group(2).strip().strip("\"'")
    return out


def wikilink(testo: str) -> list[str]:
    out: list[str] = []
    for m in _WIKILINK.finditer(_CODICE.sub("", testo)):
        target = m.group(1).split("|")[0].split("#")[0].strip()
        if target and target not in out:
            out.append(target)
    return out


def righe_corpo(testo: str) -> int:
    corpo = _FM.sub("", testo, count=1).strip("\n")
    return len(corpo.splitlines()) if corpo else 0


def note_esistenti(brain_root: Path) -> set[str]:
    """Names a wikilink can resolve to: note stems of the corpus plus the entry points."""
    nomi = set(PUNTI_INGRESSO)
    for md in brain_root.rglob("*.md"):
        parti = md.relative_to(brain_root).parts
        if md.name in FILE_GESTITI or any(p in CARTELLE_ESCLUSE for p in parti[:-1]):
            continue
        nomi.add(md.stem)
    return nomi


def classification_cartella(brain_root: Path, nota: str) -> str | None:
    """`classification` of the nearest `_index.md` going up from the note's folder."""
    cartella = PurePosixPath(nota).parent
    while True:
        indice = brain_root / cartella / "_index.md"
        if indice.is_file():
            fm = frontmatter(indice.read_text(encoding="utf-8")) or {}
            if fm.get("classification"):
                return fm["classification"]
        if cartella == PurePosixPath("."):
            return None
        cartella = cartella.parent


def valida(nota: str, testo: str, brain_root: Path) -> Esito:
    """Check a note (path relative to brain/) against the form rules of the brain."""
    testo = testo.replace("\r\n", "\n")
    problemi: list[Problema] = []

    fm = frontmatter(testo)
    if fm is None:
        problemi.append(Problema(regola="frontmatter", messaggio="manca il frontmatter in testa"))
        fm = {}
    else:
        for campo in CAMPI_OBBLIGATORI:
            if not fm.get(campo):
                problemi.append(
                    Problema(regola="frontmatter", messaggio=f"campo mancante: {campo}")
                )

    nome = PurePosixPath(nota).stem
    indice = nome in INDICI
    noti = note_esistenti(brain_root) | {nome}
    link = wikilink(testo)
    rotti = [t for t in link if t not in noti]
    for t in rotti:
        problemi.append(Problema(regola="wikilink", messaggio=f"[[{t}]] non porta a nessuna nota"))
    validi = [t for t in link if t in noti and t != nome and t not in INDICI | PUNTI_INGRESSO]
    if not indice and len(validi) < MIN_WIKILINK:
        problemi.append(
            Problema(
                regola="wikilink",
                messaggio=f"{len(validi)} wikilink verso altre note (minimo {MIN_WIKILINK})",
            )
        )

    righe = righe_corpo(testo)
    if righe > MAX_RIGHE:
        problemi.append(
            Problema(regola="lunghezza", messaggio=f"{righe} righe di corpo (massimo {MAX_RIGHE})")
        )

    ereditata = classification_cartella(brain_root, nota)
    propria = fm.get("classification")
    if propria and propria not in LIVELLI:
        problemi.append(
            Problema(regola="classification", messaggio=f"classification sconosciuta: {propria}")
        )
    elif propria and ereditata and LIVELLI[propria] < LIVELLI.get(ereditata, 0):
        problemi.append(
            Problema(
                regola="classification",
                messaggio=f"la cartella è {ereditata}: la nota non può essere meno riservata",
            )
        )

    return Esito(
        valida=not problemi,
        problemi=problemi,
        wikilink_validi=len(validi),
        righe_corpo=righe,
        classification=propria or ereditata,
    )
