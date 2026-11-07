"""Access through the Life gate: the node trusts no header, it asks the operator.

The gate puts the member's token in `Authorization` (or Caddy's `X-Life-Person`);
`GET {LIFE_OPERATOR_URL}/api/people/me` validates it and returns the person, so a forged
header is a 401. Answers are cached briefly, keyed by a hash of the token.
"""

import hashlib
import time
from typing import Any

import httpx
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel

from .config import settings
from .identity import Utente

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_TTL = 45.0
# Life roles that promote and write anywhere; any other member is an area editor.
_ADMIN_ROLES = {"owner", "admin"}


def _token(request: Request) -> str | None:
    for name in ("x-life-person", "authorization"):
        value = request.headers.get(name, "")
        if value.startswith("Bearer ") and value[7:].strip():
            return value[7:].strip()
    return None


async def _people_me(token: str) -> dict[str, Any] | None:
    key = hashlib.sha256(token.encode()).hexdigest()
    hit = _CACHE.get(key)
    if hit and hit[0] > time.monotonic():
        return hit[1]
    if not settings.life_operator_url:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "LIFE_OPERATOR_URL not set")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                f"{settings.life_operator_url.rstrip('/')}/api/people/me",
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "gate unreachable") from None
    data = r.json() if r.status_code == 200 else None
    if not isinstance(data, dict):
        return None
    _CACHE[key] = (time.monotonic() + _TTL, data)
    return data


async def utente_corrente(request: Request) -> Utente:
    token = _token(request)
    me = await _people_me(token) if token else None
    if me is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Missing or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    roles = {
        m.get("role")
        for m in me.get("memberships", [])
        if not settings.life_instance or m.get("instance") == settings.life_instance
    }
    if me.get("life_role") in _ADMIN_ROLES:
        roles.add("admin")
    roles.discard(None)
    if not roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this instance")
    ids = me.get("identities") or {}
    email = ids.get("email") or ids.get("google") or ""
    return Utente(
        id=int(me["person_id"]),
        username=email or str(me["person_id"]),
        nome=me.get("display_name") or email,
        email=email,
        ruoli=["admin"] if roles & _ADMIN_ROLES else ["manager"],
    )


class UtenteOut(BaseModel):
    id: int
    username: str
    nome: str
    email: str
    ruoli: list[str]
    is_admin: bool
    portali: list[str] = []


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=UtenteOut)
async def me(utente: Utente = Depends(utente_corrente)) -> UtenteOut:
    return UtenteOut(**utente.model_dump(), is_admin=utente.is_admin)


def mount(app: FastAPI) -> None:
    app.include_router(router)
