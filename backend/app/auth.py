"""Authentication provider of the node, chosen by `AUTH_PROVIDER`.

- `gate` (default): the Life gate, see `gate.py`. The only provider of the public node.
- any other value names a module of `app/local/` (a tree-specific login): a local option for
  users outside the gate. The core never imports one by name, so it stays optional.

A provider module exposes `utente_corrente` (the FastAPI dependency) and `mount(app)`.
"""

import importlib

from .config import settings
from .identity import Utente  # noqa: F401  (re-exported)

_provider = importlib.import_module(
    ".gate" if settings.auth_provider == "gate" else f".local.{settings.auth_provider}",
    __package__,
)

utente_corrente = _provider.utente_corrente
mount = _provider.mount
