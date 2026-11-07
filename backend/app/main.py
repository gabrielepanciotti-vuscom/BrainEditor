"""BrainEditor entry point (FastAPI). All but health and login need an authenticated user."""

from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

from .aree import Area, carica_aree, trova_area
from . import auth
from .auth import Utente, utente_corrente
from .config import settings
from .lettura import Domanda, VoceNota, domande_aperte, elenca_note, risolvi_percorsi
from .revisione import (
    Autore,
    Commit,
    ErroreRevisione,
    Revisione,
    VoceCronologia,
    imposta_stato,
    leggi_stato,
    normalizza_nota,
)
from .validatori import Esito, valida

app = FastAPI(title=settings.app_name)
auth.mount(app)

UtenteCorrente = Annotated[Utente, Depends(utente_corrente)]


def get_revisione() -> Revisione:
    return Revisione(
        settings.brain_root,
        settings.worktrees_root,
        base=settings.revision_base,
        committer=Autore(nome=settings.git_committer_name, email=settings.git_committer_email),
    )


class Modifica(BaseModel):
    contenuto: str
    messaggio: str = ""


class Bozza(BaseModel):
    contenuto: str


class Nota(BaseModel):
    nota: str
    contenuto: str
    stato: str | None
    # Open review branch, None when the text comes from the shared checkout.
    branch: str | None


class Promozione(BaseModel):
    stato: Literal["review", "active"]


def _autore(utente: Utente) -> Autore:
    return Autore(nome=utente.nome, email=utente.email)


def _come_salvata(contenuto: str) -> str:
    """The text as it will be committed: a save always sets status back to draft."""
    try:
        return imposta_stato(contenuto.replace("\r\n", "\n"), "draft")
    except ErroreRevisione:
        return contenuto  # no frontmatter: the validator says so


def _verifica_area(utente: Utente, nota: str) -> None:
    """Area owners write only in their area's folders; admins anywhere."""
    if utente.is_admin:
        return
    cartelle = {
        c for a in carica_aree() if utente.email in a.responsabili for c in a.cartelle_brain
    }
    if nota.split("/", 1)[0] not in cartelle:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "nota fuori dalle cartelle della tua area")


@app.get("/api/health")
async def health() -> dict[str, str]:
    brain = "ok" if settings.brain_root.is_dir() else "missing"
    return {"status": "ok", "service": "brain-editor", "brain": brain}


@app.get("/api/aree", response_model=list[Area])
async def aree(utente: UtenteCorrente) -> list[Area]:
    return carica_aree()


def _area(area_id: str) -> Area:
    area = trova_area(area_id)
    if area is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"area {area_id} inesistente")
    return area


@app.get("/api/aree/{area_id}/note", response_model=list[VoceNota])
def note_area(area_id: str, utente: UtenteCorrente) -> list[VoceNota]:
    """Notes of the area's brain folders, as published on the shared checkout."""
    return elenca_note(settings.brain_root, _area(area_id).cartelle_brain)


@app.get("/api/aree/{area_id}/domande", response_model=list[Domanda])
def domande_area(area_id: str, utente: UtenteCorrente) -> list[Domanda]:
    """Open questions of the internal register for this area (the register is internal-only)."""
    area = _area(area_id)
    registro = settings.brain_root / settings.open_questions_note
    if not settings.open_questions_note or not registro.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "registro domande aperte non trovato")
    domande = domande_aperte(registro.read_text(encoding="utf-8"), area.prefissi_domande)
    return risolvi_percorsi(settings.brain_root, domande)


@app.get("/api/note/{nota:path}", response_model=Nota)
def leggi_nota(
    nota: str,
    utente: UtenteCorrente,
    rev: Annotated[Revisione, Depends(get_revisione)],
) -> Nota:
    try:
        nota = normalizza_nota(nota)
    except ErroreRevisione as e:
        raise HTTPException(422, str(e)) from e
    try:
        testo, branch = rev.leggi(nota)
    except ErroreRevisione as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e
    return Nota(nota=nota, contenuto=testo, stato=leggi_stato(testo), branch=branch)


@app.post("/api/validazione/{nota:path}", response_model=Esito)
def valida_nota(
    nota: str,
    bozza: Bozza,
    utente: UtenteCorrente,
    rev: Annotated[Revisione, Depends(get_revisione)],
) -> Esito:
    """Live check for the editor: pure, writes nothing."""
    try:
        nota = normalizza_nota(nota)
    except ErroreRevisione as e:
        raise HTTPException(422, str(e)) from e
    return valida(nota, _come_salvata(bozza.contenuto), rev.brain_root)


@app.put("/api/note/{nota:path}", response_model=Commit)
def salva_nota(
    nota: str,
    modifica: Modifica,
    utente: UtenteCorrente,
    rev: Annotated[Revisione, Depends(get_revisione)],
) -> Commit:
    try:
        nota = normalizza_nota(nota)
        _verifica_area(utente, nota)
        esito = valida(nota, _come_salvata(modifica.contenuto), rev.brain_root)
        if not esito.valida:
            raise HTTPException(
                422,
                {
                    "messaggio": "nota non valida",
                    "problemi": [p.model_dump() for p in esito.problemi],
                },
            )
        return rev.salva(nota, modifica.contenuto, _autore(utente), modifica.messaggio)
    except ErroreRevisione as e:
        raise HTTPException(422, str(e)) from e


@app.post("/api/promozione/{nota:path}", response_model=Commit)
def promuovi_nota(
    nota: str,
    promozione: Promozione,
    utente: UtenteCorrente,
    rev: Annotated[Revisione, Depends(get_revisione)],
) -> Commit:
    if not utente.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "solo admin promuove gli stati")
    try:
        return rev.promuovi(nota, promozione.stato, _autore(utente))
    except ErroreRevisione as e:
        raise HTTPException(422, str(e)) from e


@app.get("/api/cronologia/{nota:path}", response_model=list[VoceCronologia])
def cronologia_nota(
    nota: str,
    utente: UtenteCorrente,
    rev: Annotated[Revisione, Depends(get_revisione)],
) -> list[VoceCronologia]:
    try:
        return rev.cronologia(nota)
    except ErroreRevisione as e:
        raise HTTPException(422, str(e)) from e
