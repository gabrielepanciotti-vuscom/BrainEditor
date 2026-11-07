from pathlib import Path

from app.auth import Utente, utente_corrente
from app.config import default_brain_root
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health() -> None:
    assert client.get("/api/health").json()["status"] == "ok"


def test_aree_come_from_the_areas_file() -> None:
    assert client.get("/api/aree").status_code == 401
    app.dependency_overrides[utente_corrente] = lambda: Utente(nome="M", email="m@example.com")
    try:
        ids = [a["id"] for a in client.get("/api/aree").json()]
    finally:
        app.dependency_overrides.clear()
    assert ids == ["general"]


def test_brain_root_comes_from_the_tree_resolver(tmp_path: Path, monkeypatch) -> None:
    from app import config

    monkeypatch.setattr(config, "_tree_root", lambda instance_id: tmp_path)
    assert default_brain_root("acme") == tmp_path / "brain"


def test_brain_root_without_life_does_not_exist(monkeypatch) -> None:
    from app import config

    monkeypatch.setattr(config, "_tree_root", lambda instance_id: None)
    assert not default_brain_root().exists()


def test_areas_file_prefers_the_tree_then_the_example(tmp_path: Path, monkeypatch) -> None:
    from app import config

    monkeypatch.setattr(config, "_tree_root", lambda instance_id: tmp_path)
    assert config.default_areas_file() == config.EXAMPLE_AREAS
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / config.TREE_AREAS_FILE).write_text("{}")
    assert config.default_areas_file() == tmp_path / "config" / config.TREE_AREAS_FILE
