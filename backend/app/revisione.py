"""Review flow: one commit per change on a per-note review branch of the brain repo.

Writes never touch the shared checkout: each review branch lives in its own git worktree
under ``settings.worktrees_root``. A commit carries only the edited note and the real
author; the service account is just the committer.
"""

import os
import re
import subprocess
import threading
from datetime import datetime
from pathlib import Path, PurePosixPath

from pydantic import BaseModel

# Forward-only lifecycle: an edit always goes back to draft, admins promote.
PROMOZIONI = {"draft": "review", "review": "active"}
BRANCH_PREFIX = "revisione/"

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_STATUS = re.compile(r"^status:[ \t]*(\S*)[ \t]*$", re.MULTILINE)


class ErroreRevisione(ValueError):
    """Invalid request (bad path, missing note, forbidden transition)."""


class Autore(BaseModel):
    nome: str
    email: str


class Commit(BaseModel):
    sha: str
    branch: str
    nota: str
    stato: str


class VoceCronologia(BaseModel):
    sha: str
    autore: str
    email: str
    data: datetime
    messaggio: str


def normalizza_nota(nota: str) -> str:
    """Path of a note relative to brain/, rejecting anything that could escape it."""
    p = PurePosixPath(nota.strip().replace("\\", "/"))
    if p.is_absolute() or not p.parts or ".." in p.parts or p.suffix != ".md":
        raise ErroreRevisione(f"percorso di nota non valido: {nota!r}")
    if any(part.startswith(".") for part in p.parts):
        raise ErroreRevisione(f"percorso di nota non valido: {nota!r}")
    # brain/private/ is gitignored knowledge: a review commit would version it.
    if p.parts[0] == "private":
        raise ErroreRevisione(f"le note private non passano dall'editor: {nota!r}")
    return p.as_posix()


def branch_per(nota: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", nota.removesuffix(".md").lower()).strip("-")
    return BRANCH_PREFIX + slug


def leggi_stato(testo: str) -> str | None:
    fm = _FRONTMATTER.match(testo)
    if not fm:
        return None
    m = _STATUS.search(fm.group(1))
    return m.group(1) if m else None


def imposta_stato(testo: str, stato: str) -> str:
    fm = _FRONTMATTER.match(testo)
    if not fm:
        raise ErroreRevisione("la nota non ha frontmatter")
    corpo = fm.group(1)
    if _STATUS.search(corpo):
        corpo = _STATUS.sub(f"status: {stato}", corpo, count=1)
    else:
        corpo = f"{corpo}\nstatus: {stato}"
    return f"---\n{corpo}\n---\n" + testo[fm.end() :]


class Revisione:
    def __init__(
        self,
        brain_root: Path,
        worktrees_root: Path,
        base: str = "main",
        committer: Autore | None = None,
    ) -> None:
        self.brain_root = brain_root
        self.repo = brain_root.parent
        self.brain_dir = brain_root.name
        self.worktrees_root = worktrees_root
        self.base = base
        self.committer = committer
        # Worktree creation and commits mutate the shared .git: serialize them.
        self._lock = threading.Lock()

    def _git(self, *args: str, cwd: Path | None = None) -> str:
        env = dict(os.environ)
        if self.committer:
            env["GIT_COMMITTER_NAME"] = self.committer.nome
            env["GIT_COMMITTER_EMAIL"] = self.committer.email
        res = subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {res.stderr.strip()}")
        return res.stdout

    def _esiste_branch(self, branch: str) -> bool:
        res = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
            cwd=self.repo,
            capture_output=True,
            check=False,
        )
        return res.returncode == 0

    def _worktree(self, branch: str) -> Path:
        path = self.worktrees_root / branch.removeprefix(BRANCH_PREFIX)
        if (path / ".git").exists():
            return path
        self.worktrees_root.mkdir(parents=True, exist_ok=True)
        self._git("worktree", "prune")
        if self._esiste_branch(branch):
            self._git("worktree", "add", str(path), branch)
        else:
            self._git("worktree", "add", "-b", branch, str(path), self.base)
        return path

    def _commit(self, wt: Path, rel: str, testo: str, autore: Autore, messaggio: str) -> str:
        file = wt / rel
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(testo, encoding="utf-8")
        self._git("add", "--", rel, cwd=wt)
        # Pathspec limits the commit to this note even if the worktree had other changes.
        self._git(
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            messaggio,
            f"--author={autore.nome} <{autore.email}>",
            "--",
            rel,
            cwd=wt,
        )
        return self._git("rev-parse", "HEAD", cwd=wt).strip()

    def salva(self, nota: str, contenuto: str, autore: Autore, messaggio: str = "") -> Commit:
        """Commit an edit on the note's review branch; the edit always goes back to draft."""
        nota = normalizza_nota(nota)
        rel = f"{self.brain_dir}/{nota}"
        testo = imposta_stato(contenuto.replace("\r\n", "\n"), "draft")
        branch = branch_per(nota)
        with self._lock:
            wt = self._worktree(branch)
            file = wt / rel
            if file.exists() and file.read_text(encoding="utf-8") == testo:
                raise ErroreRevisione("nessuna modifica rispetto all'ultima revisione")
            sha = self._commit(wt, rel, testo, autore, messaggio or f"brain: modifica {nota}")
        return Commit(sha=sha, branch=branch, nota=nota, stato="draft")

    def leggi(self, nota: str) -> tuple[str, str | None]:
        """Text of the note and its open review branch; without a branch, the shared checkout."""
        nota = normalizza_nota(nota)
        branch = branch_per(nota)
        if self._esiste_branch(branch):
            try:
                return self._git("show", f"{branch}:{self.brain_dir}/{nota}"), branch
            except RuntimeError:
                pass
        file = self.brain_root / nota
        if not file.is_file():
            raise ErroreRevisione("nota inesistente")
        return file.read_text(encoding="utf-8"), None

    def promuovi(self, nota: str, stato: str, autore: Autore) -> Commit:
        """draft -> review -> active on the review branch. Role checks live in the API."""
        nota = normalizza_nota(nota)
        rel = f"{self.brain_dir}/{nota}"
        branch = branch_per(nota)
        with self._lock:
            if not self._esiste_branch(branch):
                raise ErroreRevisione("la nota non ha una revisione aperta")
            wt = self._worktree(branch)
            file = wt / rel
            if not file.exists():
                raise ErroreRevisione("nota inesistente sul branch di revisione")
            testo = file.read_text(encoding="utf-8")
            attuale = leggi_stato(testo)
            if PROMOZIONI.get(attuale or "") != stato:
                raise ErroreRevisione(f"transizione non ammessa: {attuale} -> {stato}")
            sha = self._commit(
                wt, rel, imposta_stato(testo, stato), autore, f"brain: {nota} {attuale} -> {stato}"
            )
        return Commit(sha=sha, branch=branch, nota=nota, stato=stato)

    def cronologia(self, nota: str) -> list[VoceCronologia]:
        """Commits touching the note: review branch if open (it includes the base), else base."""
        nota = normalizza_nota(nota)
        branch = branch_per(nota)
        ref = branch if self._esiste_branch(branch) else self.base
        out = self._git(
            "log", "--format=%H%x1f%an%x1f%ae%x1f%aI%x1f%s", ref, "--", f"{self.brain_dir}/{nota}"
        )
        voci = []
        for riga in out.splitlines():
            sha, nome, email, data, msg = riga.split("\x1f", 4)
            voci.append(
                VoceCronologia(
                    sha=sha,
                    autore=nome,
                    email=email,
                    data=datetime.fromisoformat(data),
                    messaggio=msg,
                )
            )
        return voci
