import subprocess
from pathlib import Path

import pytest
from app.auth import Utente, utente_corrente
from app.main import app, get_revisione
from app.revisione import Autore, ErroreRevisione, Revisione, leggi_stato, normalizza_nota
from fastapi.testclient import TestClient

NOTA = "01-mercato/prezzo.md"
TESTO = (
    "---\ntitle: Prezzo\nsummary: Prezzo\ntags: [mercato]\nstatus: active\n"
    "created: 2026-10-19\nupdated: 2026-10-19\n---\n\nCorpo.\n\n[[pun]] [[psv]] [[spread]]\n"
)
VICINE = ("pun", "psv", "spread")
MARIO = Autore(nome="Bob Example", email="bob@example.com")
GABRIELE = Autore(nome="Alice Example", email="alice@example.com")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    repo = tmp_path / "acme-tree"
    (repo / "brain" / "01-mercato").mkdir(parents=True)
    (repo / "brain" / NOTA).write_text(TESTO, encoding="utf-8")
    for nome in VICINE:
        (repo / "brain" / "01-mercato" / f"{nome}.md").write_text("x\n", encoding="utf-8")
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
    return repo


@pytest.fixture
def rev(repo: Path, tmp_path: Path) -> Revisione:
    return Revisione(
        repo / "brain",
        tmp_path / "worktrees",
        committer=Autore(nome="BrainEditor", email="service@example.com"),
    )


def test_edit_is_one_commit_on_review_branch_with_real_author(rev: Revisione, repo: Path) -> None:
    head_prima = git(repo, "rev-parse", "HEAD")
    c = rev.salva(NOTA, TESTO.replace("Corpo.", "Corpo nuovo."), MARIO)

    assert c.branch == "revisione/01-mercato-prezzo" and c.stato == "draft"
    assert git(repo, "log", "-1", "--format=%an <%ae>|%cn", c.sha) == (
        "Bob Example <bob@example.com>|BrainEditor"
    )
    assert git(repo, "show", "--name-only", "--format=", c.sha) == f"brain/{NOTA}"
    assert git(repo, "rev-list", "--count", f"main..{c.branch}") == "1"
    # Shared checkout untouched: same branch, same HEAD, clean tree.
    assert git(repo, "branch", "--show-current") == "main"
    assert git(repo, "rev-parse", "HEAD") == head_prima
    assert git(repo, "status", "--porcelain") == ""
    assert (repo / "brain" / NOTA).read_text(encoding="utf-8") == TESTO


def test_edit_forces_draft_and_promotion_is_forward_only(rev: Revisione, repo: Path) -> None:
    rev.salva(NOTA, TESTO.replace("Corpo.", "Altro."), MARIO)
    branch = "revisione/01-mercato-prezzo"
    assert leggi_stato(git(repo, "show", f"{branch}:brain/{NOTA}") + "\n") == "draft"

    with pytest.raises(ErroreRevisione):
        rev.promuovi(NOTA, "active", GABRIELE)
    rev.promuovi(NOTA, "review", GABRIELE)
    rev.promuovi(NOTA, "active", GABRIELE)
    assert "status: active" in git(repo, "show", f"{branch}:brain/{NOTA}")
    assert git(repo, "rev-list", "--count", f"main..{branch}") == "3"


def test_second_edit_reuses_branch_and_noop_is_rejected(rev: Revisione) -> None:
    nuovo = TESTO.replace("Corpo.", "Uno.")
    rev.salva(NOTA, nuovo, MARIO)
    with pytest.raises(ErroreRevisione):
        rev.salva(NOTA, nuovo, MARIO)
    rev.salva(NOTA, TESTO.replace("Corpo.", "Due."), GABRIELE)
    autori = [v.autore for v in rev.cronologia(NOTA)]
    assert autori == ["Alice Example", "Bob Example", "t"]


def test_new_note_is_created_on_its_branch(rev: Revisione, repo: Path) -> None:
    c = rev.salva("01-mercato/nuova.md", "---\ntitle: Nuova\n---\n\nTesto.\n", MARIO)
    assert "status: draft" in git(repo, "show", f"{c.branch}:brain/01-mercato/nuova.md")
    assert not (repo / "brain" / "01-mercato" / "nuova.md").exists()


@pytest.mark.parametrize(
    "nota",
    [
        "private/segreto.md",
        "../etc/passwd.md",
        "/abs.md",
        "a/../../b.md",
        "nota.txt",
        ".git/x.md",
        "",
    ],
)
def test_paths_escaping_brain_are_rejected(nota: str) -> None:
    with pytest.raises(ErroreRevisione):
        normalizza_nota(nota)


# --- API -------------------------------------------------------------------


@pytest.fixture
def client(rev: Revisione):
    app.dependency_overrides[get_revisione] = lambda: rev
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(utente: Utente) -> None:
    app.dependency_overrides[utente_corrente] = lambda: utente


def test_write_endpoints_require_login(client: TestClient) -> None:
    r = client.put(f"/api/note/{NOTA}", json={"contenuto": TESTO})
    assert r.status_code == 401


def test_owner_outside_area_is_forbidden(client: TestClient) -> None:
    _login(Utente(nome="Bob Example", email="bob@example.com", ruoli=["user"]))
    r = client.put(f"/api/note/{NOTA}", json={"contenuto": TESTO.replace("Corpo.", "X.")})
    assert r.status_code == 403


def test_admin_edits_promotes_and_reads_history(client: TestClient) -> None:
    _login(Utente(nome="Alice Example", email="alice@example.com", ruoli=["admin"]))
    r = client.put(f"/api/note/{NOTA}", json={"contenuto": TESTO.replace("Corpo.", "Y.")})
    assert r.status_code == 200 and r.json()["stato"] == "draft"
    assert client.post(f"/api/promozione/{NOTA}", json={"stato": "review"}).json()["stato"] == (
        "review"
    )
    assert client.post(f"/api/promozione/{NOTA}", json={"stato": "review"}).status_code == 422
    assert len(client.get(f"/api/cronologia/{NOTA}").json()) == 3


def test_invalid_note_is_not_committed(client: TestClient, repo: Path) -> None:
    _login(Utente(nome="Alice Example", email="alice@example.com", ruoli=["admin"]))
    r = client.put(f"/api/note/{NOTA}", json={"contenuto": TESTO.replace("[[spread]]", "")})
    assert r.status_code == 422
    assert [p["regola"] for p in r.json()["detail"]["problemi"]] == ["wikilink"]
    assert git(repo, "branch", "--list", "revisione/*") == ""


def test_read_note_follows_the_review_branch(client: TestClient) -> None:
    _login(Utente(nome="Alice Example", email="alice@example.com", ruoli=["admin"]))
    prima = client.get(f"/api/note/{NOTA}").json()
    assert prima["branch"] is None and prima["stato"] == "active"
    client.put(f"/api/note/{NOTA}", json={"contenuto": TESTO.replace("Corpo.", "Z.")})
    dopo = client.get(f"/api/note/{NOTA}").json()
    assert dopo["branch"] == "revisione/01-mercato-prezzo" and dopo["stato"] == "draft"
    assert "Z." in dopo["contenuto"]
    assert client.get("/api/note/01-mercato/assente.md").status_code == 404


def test_validation_endpoint_ignores_status_and_writes_nothing(client: TestClient) -> None:
    _login(Utente(nome="Bob Example", email="bob@example.com", ruoli=["manager"]))
    senza_stato = TESTO.replace("status: active\n", "")
    esito = client.post(f"/api/validazione/{NOTA}", json={"contenuto": senza_stato}).json()
    assert esito["valida"] and esito["wikilink_validi"] == 3


def test_only_admin_promotes(client: TestClient) -> None:
    _login(Utente(nome="Bob Example", email="bob@example.com", ruoli=["user"]))
    assert client.post(f"/api/promozione/{NOTA}", json={"stato": "review"}).status_code == 403
