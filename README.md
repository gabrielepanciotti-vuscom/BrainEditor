# BrainEditor

A small web editor for the markdown notes of a Life tree's `brain/`, for people who do not use git.

- Notes stay plain markdown in the tree; the node has **no database**.
- One edit = one commit on a review branch of the tree repo; an admin promotes `draft` -> `review` -> `active`.
- Notes are checked live: complete frontmatter, at least 3 wikilinks, at most 300 lines, `classification` inherited from the folder.
- Access goes through the Life gate (`AUTH_PROVIDER=gate`, default); a tree-specific login can be added as a module under `backend/app/local/`.

Stack: FastAPI (Python 3.13) + React/Vite on `@suite/design-system`. Backend `8035`, frontend `3035`.

## Run
```bash
cp .env.example .env            # LIFE_INSTANCE selects the tree whose brain is edited
python3.13 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
cd backend && ../.venv/bin/uvicorn app.main:app --port 8035
cd frontend && npm install && npm run dev      # Node 22+
```

## Test
```bash
.venv/bin/python -m pytest backend
cd frontend && npm test
```

Areas are read from `<instance>/config/brain-editor-areas.json`, falling back to `config/areas.example.json` (example data only).
