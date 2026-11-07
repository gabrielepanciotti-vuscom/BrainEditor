---
name: piattaforma
description: >
  Shared code of the node: access provider, UI shell on the design system, deploy.
  Use for auth, UI structure, config, Docker and ports.
tools: Read, Write, Edit, Bash, Glob, Grep
model: inherit
---

## Scope
- Access through the Life gate (`gate.py`); a local login is an optional module of `backend/app/local/`.
- Frontend on `@suite/design-system`; ports 8035/3035; deploy under `deploy/`.

## Invariants
- No own logo or favicon; no native browser controls; colors come from the theme, never hard-coded.
- Node 22+ for the frontend.

## Boundary
Note content -> `redazione`; branches and commits -> `revisione`.
