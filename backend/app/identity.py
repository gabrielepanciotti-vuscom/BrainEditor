"""Who is calling: the user type of the node, independent of how they were identified."""

from pydantic import BaseModel

RUOLI_ADMIN = {"admin", "superadmin"}


class Utente(BaseModel):
    id: int = 0
    username: str = ""
    # «First Last», else the username: the author of review commits.
    nome: str
    email: str
    ruoli: list[str] = []

    @property
    def is_admin(self) -> bool:
        return bool(RUOLI_ADMIN & set(self.ruoli))
