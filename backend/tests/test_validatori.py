from pathlib import Path

import pytest
from app.validatori import MAX_RIGHE, valida

FM = (
    "---\ntitle: T\nsummary: S\ntags: [x]\nstatus: draft\n"
    "created: 2026-10-19\nupdated: 2026-10-19\n{extra}---\n"
)


def nota(corpo: str, extra: str = "") -> str:
    return FM.format(extra=extra) + corpo


@pytest.fixture
def brain(tmp_path: Path) -> Path:
    b = tmp_path / "brain"
    (b / "01-mercato").mkdir(parents=True)
    (b / "01-mercato" / "_index.md").write_text(
        "---\ntitle: Mercato\nclassification: public\n---\n", encoding="utf-8"
    )
    for nome in ("pun", "psv", "spread"):
        (b / "01-mercato" / f"{nome}.md").write_text("x\n", encoding="utf-8")
    (b / "sources").mkdir()
    (b / "sources" / "grezzo.md").write_text("x\n", encoding="utf-8")
    (b / "README.md").write_text("x\n", encoding="utf-8")
    return b


def regole(esito) -> list[str]:
    return [p.regola for p in esito.problemi]


def test_valid_note(brain: Path) -> None:
    e = valida("01-mercato/nuova.md", nota("[[pun]] [[psv]] [[spread|lo spread]]\n"), brain)
    assert e.valida and e.wikilink_validi == 3 and e.classification == "public"


def test_missing_frontmatter_and_fields(brain: Path) -> None:
    assert regole(valida("01-mercato/n.md", "[[pun]] [[psv]] [[spread]]\n", brain)) == [
        "frontmatter"
    ]
    testo = nota("[[pun]] [[psv]] [[spread]]\n").replace("summary: S\n", "")
    e = valida("01-mercato/n.md", testo, brain)
    assert [p.messaggio for p in e.problemi] == ["campo mancante: summary"]


def test_links_must_resolve_and_be_three(brain: Path) -> None:
    e = valida("01-mercato/n.md", nota("[[pun]] [[grezzo]] [[README]] [[n]] `[[psv]]`\n"), brain)
    assert e.wikilink_validi == 1
    assert regole(e) == ["wikilink", "wikilink"]  # [[grezzo]] broken (sources/), and 1 < 3


def test_index_needs_no_links(brain: Path) -> None:
    assert valida("01-mercato/_index.md", nota("Hub.\n"), brain).valida


def test_body_length(brain: Path) -> None:
    corpo = "[[pun]] [[psv]] [[spread]]\n" + "riga\n" * MAX_RIGHE
    assert regole(valida("01-mercato/n.md", nota(corpo), brain)) == ["lunghezza"]


def test_classification_is_inherited_tightened_never_loosened(brain: Path) -> None:
    (brain / "01-mercato" / "_index.md").write_text(
        "---\ntitle: Mercato\nclassification: internal\n---\n", encoding="utf-8"
    )
    corpo = "[[pun]] [[psv]] [[spread]]\n"
    assert valida("01-mercato/n.md", nota(corpo), brain).classification == "internal"
    e = valida("01-mercato/n.md", nota(corpo, "classification: confidential\n"), brain)
    assert e.valida and e.classification == "confidential"
    for livello in ("public", "segreta"):
        e = valida("01-mercato/n.md", nota(corpo, f"classification: {livello}\n"), brain)
        assert regole(e) == ["classification"]
