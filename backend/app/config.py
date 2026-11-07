"""Runtime configuration. Brain and areas come from the tree (via suite_core.knowledge), env overrides."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
# The areas shipped with the node: one neutral area, replaced by the tree's own file.
EXAMPLE_AREAS = REPO_ROOT / "config" / "areas.example.json"
# Name of the tree's areas file, under `<instance>/config/`.
TREE_AREAS_FILE = "brain-editor-areas.json"


def _tree_root(instance_id: str) -> Path | None:
    """Instance directory from the Life resolver, None when Life is not around."""
    try:
        from suite_core.knowledge import KnowledgeError, instance_root
    except ImportError:
        return None
    try:
        return instance_root(instance_id or None)
    except KnowledgeError:
        return None


def default_brain_root(instance_id: str = "") -> Path:
    """`<tree>/brain`; a path that does not exist (health says `missing`) when unresolved."""
    root = _tree_root(instance_id)
    return root / "brain" if root else REPO_ROOT / "var" / "no-brain"


def default_areas_file(instance_id: str = "") -> Path:
    root = _tree_root(instance_id)
    candidate = root / "config" / TREE_AREAS_FILE if root else None
    return candidate if candidate and candidate.is_file() else EXAMPLE_AREAS


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    app_name: str = "BrainEditor"
    app_port: int = 8035
    # Tree whose brain is edited; empty = the device's default instance.
    life_instance: str = os.environ.get("LIFE_INSTANCE", "")
    brain_root: Path = default_brain_root(os.environ.get("LIFE_INSTANCE", ""))
    areas_file: Path = default_areas_file(os.environ.get("LIFE_INSTANCE", ""))
    # Internal register of open questions, relative to the brain root; empty = no register.
    open_questions_note: str = ""
    # Review branches get their own worktrees here: never a checkout in the shared clone.
    worktrees_root: Path = REPO_ROOT / "var" / "worktrees"
    revision_base: str = "main"
    # Committer of review commits; the author is always the real user.
    git_committer_name: str = "BrainEditor"
    git_committer_email: str = "brain-editor@example.com"
    # Access: `gate` (Life gate, asks LIFE_OPERATOR_URL) or the name of a module in app/local/.
    auth_provider: str = "gate"
    life_operator_url: str = ""
    # Options of a local login provider (unused by the gate): shared DB and JWT secret.
    # Unset -> that login answers 503, never a token signed with an empty key.
    database_url: str = ""
    jwt_secret: str = ""
    jwt_expire_minutes: int = 480


settings = Settings()
