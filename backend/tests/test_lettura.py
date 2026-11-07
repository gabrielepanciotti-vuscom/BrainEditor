import json
from pathlib import Path

import pytest
from app.auth import Utente, utente_corrente
from app.config import settings
from app.lettura import domande_aperte, elenca_note
from app.main import app
from fastapi.testclient import TestClient

REGISTRO = """---
title: Registro
---

## Servizio Clienti

| id | domanda | nota interessata | perché serve |
|---|---|---|---|
| SC-01 | **Cascia attiva?** | [[sportelli]], [[canali]] | Il sito la pubblica |
| SC-03 | **Autolettura luce**: chiusa il 13/10/2026. | | |

## Fatturazione

| id | domanda | nota interessata | perché serve |
|---|---|---|---|
| FI-01 | ~~**Calendario gas**~~ **Chiusa il 12/10/2026** | [[calendario]] | — |
| FI-02 | **Fatturazione mensile** | [[calendario]] | Nessun calendario |

## Ufficio Offerte

| UO-01 | **Onere di recesso** | [[offerte]] | Serve |
"""


def _nota(path: Path, titolo: str, stato: str = "active") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntitle: {titolo}\nstatus: {stato}\nupdated: 2026-10-19\n---\n", encoding="utf-8"
    )


@pytest.fixture
def brain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    b = tmp_path / "brain"
    _nota(b / "15-customer-service" / "sportelli.md", "Sportelli")
    _nota(b / "15-customer-service" / "sub" / "canali.md", "Canali", "draft")
    _nota(b / "05-bill-and-price-components" / "calendario.md", "Calendario")
    (b / "15-customer-service" / "_index.md").write_text("---\ntitle: Hub\n---\n", encoding="utf-8")
    (b / "entities").mkdir()
    (b / "entities" / "registro.md").write_text(REGISTRO, encoding="utf-8")
    areas = tmp_path / "areas.json"
    areas.write_text(
        json.dumps(
            {
                "aree": [
                    {
                        "id": "sc",
                        "nome": "Service",
                        "cartelle_brain": ["15-customer-service"],
                        "prefissi_domande": ["SC"],
                    },
                    {
                        "id": "fi",
                        "nome": "Billing",
                        "cartelle_brain": ["05-bill-and-price-components", "15-customer-service"],
                        "prefissi_domande": ["FI"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "areas_file", areas)
    monkeypatch.setattr(settings, "brain_root", b)
    monkeypatch.setattr(settings, "open_questions_note", "entities/registro.md")
    return b


@pytest.fixture
def client(brain: Path):
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login() -> None:
    app.dependency_overrides[utente_corrente] = lambda: Utente(
        nome="Alice", email="alice@example.com", ruoli=["admin"]
    )


def test_open_questions_skip_closed_rows_and_other_areas() -> None:
    ids = [d.id for d in domande_aperte(REGISTRO, ["SC", "FI"])]
    assert ids == ["SC-01", "FI-02"]


def test_open_questions_carry_linked_notes_and_reason() -> None:
    (d,) = domande_aperte(REGISTRO, ["UO"])
    assert d.note == ["offerte"]
    assert d.perche == "Serve"


def test_notes_of_folders_are_recursive_without_hubs(brain: Path) -> None:
    voci = elenca_note(brain, ["15-customer-service", "manca"])
    assert [v.nota for v in voci] == [
        "15-customer-service/sportelli.md",
        "15-customer-service/sub/canali.md",
    ]
    assert voci[1].stato == "draft"


def test_area_reading_requires_login(client: TestClient) -> None:
    assert client.get("/api/aree/sc/note").status_code == 401
    assert client.get("/api/aree/sc/domande").status_code == 401


def test_area_notes_and_questions(client: TestClient) -> None:
    _login()
    note = client.get("/api/aree/fi/note").json()
    assert [n["nota"] for n in note] == [
        "05-bill-and-price-components/calendario.md",
        "15-customer-service/sportelli.md",
        "15-customer-service/sub/canali.md",
    ]
    (domanda,) = client.get("/api/aree/fi/domande").json()
    assert domanda["id"] == "FI-02"
    assert domanda["percorsi"] == {"calendario": "05-bill-and-price-components/calendario.md"}


def test_unknown_area_is_404(client: TestClient) -> None:
    _login()
    assert client.get("/api/aree/xx/note").status_code == 404
