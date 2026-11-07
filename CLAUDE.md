# BrainEditor

Public node of Life (slug `brainEditor`): a web editor for the notes of a tree's `brain/`, for people who do not use git. Notes stay markdown in the tree; the node has no DB. Decision of 2026-11-06 (core / showcase / local).

## Layers
- **Core** (this repo, public, no organization-specific reference): `backend/app/`, `frontend/src/`. Brain and areas are resolved from the tree with `suite_core.knowledge` (`LIFE_INSTANCE`, overrides `BRAIN_ROOT`/`AREAS_FILE`).
- **Showcase**: the tree's `theme.config.json`; the frontend is on `@suite/design-system`.
- **Local**: a tree-specific login lives in `backend/app/local/` (selected by `AUTH_PROVIDER=<module>`), with its own deploy files, in a private repo or in the tree. Never committed here.
Access of the public node comes from the Life gate (`gate.py` -> `LIFE_OPERATOR_URL/api/people/me`).

## Stack and ports
FastAPI (Python 3.13, `.venv/`) + React/Vite on `@suite/design-system`. Backend **8035**, frontend **3035**. Name: `brain-editor.life.local`.

## Structure
- `backend/app/` - `main.py` (API), `auth.py` (picks the provider), `identity.py` (`Utente`), `gate.py` (Life gate), `revisione.py` (branches, commits, states), `validatori.py` (form rules), `config.py` (brain/areas from the tree), `aree.py`, `lettura.py` (notes per area, open questions)
- `config/areas.example.json` - neutral example area; the real areas live in the tree
- `frontend/src/` - `app/` layout and navigation, `aree/` Areas page, `editor/` editor with live check, `auth/` access
- `.claude/agents/` - redazione (content), revisione (branches/states), piattaforma (auth/UI/deploy)

## Commands
- Backend: `.venv/bin/python -m pytest backend` - run `cd backend && ../.venv/bin/uvicorn app.main:app --port 8035`
- Frontend (**Node 22+**): `cd frontend && npm install && npm run dev`; tests `npm test`

## Project rules
- One edit = one commit on a review branch of the tree repo; an admin promotes `draft` -> `review`, `active` only after.
- Notes need frontmatter, at least 3 wikilinks, at most 300 lines; `classification` sits on the folder; `status: draft` never leaves the tree.
- Roles: `admin` promotes and writes anywhere; area owners write in their area's folders.
