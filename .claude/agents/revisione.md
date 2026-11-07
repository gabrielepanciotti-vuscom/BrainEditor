---
name: revisione
description: >
  Review flow of the changes: one commit per change on a review branch, promotion draft -> review -> active.
  Use for branches, commits in the tree repo, history and state promotion.
tools: Read, Write, Edit, Bash, Glob, Grep
model: inherit
---

## Scope
- One commit per change, on a review branch of the tree repo (never directly on `main`).
- State transitions `draft` -> `review` -> `active`; only an admin promotes.
- Note history (git log) shown to the user.

## Invariants
- Git writes go through a dedicated worktree: never `checkout` in the tree's shared checkout.
- A commit holds only the edited note and the real author, not a service account.

## Boundary
Note content and validation -> `redazione`; auth and deploy -> `piattaforma`.
