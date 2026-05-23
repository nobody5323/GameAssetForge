# Task Plan: Implement GameAsset Forge MVP

## Goal
Build a runnable GameAsset Forge MVP matching the 12-PR plan: React/Vite frontend, FastAPI backend, mock asset generation, quality inspection, manifest/zip export, simulated cloud upload, and documentation.

## Current Phase
PR 5

## Phases

### Phase 1: Requirements & Discovery
- [x] Read the engineering design document.
- [x] Confirm repository is effectively empty except for the design document.
- [x] Confirm Python, Node, and npm are available.
- **Status:** complete

### Phase 2: Planning & Structure
- [x] Use React + Vite and Python FastAPI.
- [x] Implement the requested 12-PR roadmap as one MVP working tree.
- [x] Preserve PR plan in docs.
- **Status:** complete

### Phase 3: PR 1 Project Bootstrap
- [x] Create repository docs and env example.
- [x] Create top-level frontend/backend/docs/storage directories.
- [x] Preserve PR plan for future branches.
- **Status:** complete

### Phase 4: PR 1 Verification
- [x] Verify only PR 1 bootstrap files remain.
- [x] Commit PR 1 in multiple small commits.
- **Status:** complete

### Phase 5: PR 2 Frontend Shell
- [x] Create React + Vite frontend project files.
- [x] Add navigation and four static workspace views.
- [x] Add package lock for reproducible installs.
- [x] Document PR 2 changes and verification.
- **Status:** complete

### Phase 6: PR 2 Verification
- [x] Run `npm install`.
- [x] Run `npm run build`.
- [x] Push PR 2 branch.
- **Status:** complete

### Phase 7: PR 3 Backend FastAPI Shell
- [x] Create FastAPI app entrypoint.
- [x] Add `/api/health` route.
- [x] Add backend module directories for later PRs.
- [x] Add pytest configuration and health endpoint test.
- [x] Document PR 3 changes and verification.
- **Status:** complete

### Phase 8: PR 3 Verification
- [x] Install backend dependencies.
- [x] Run `python -m pytest`.
- [x] Confirm Uvicorn foreground startup output.
- [x] Push PR 3 branch.
- **Status:** complete

### Phase 9: PR 4 Generation Form
- [x] Add editable frontend generation form.
- [x] Add asset row add/remove/enable controls.
- [x] Add live request JSON preview.
- [x] Extract request builder for testing.
- [x] Add frontend unit tests.
- **Status:** complete

### Phase 10: PR 4 Verification
- [x] Run `npm test`.
- [x] Run `npm run build`.
- [x] Push PR 4 branch.
- **Status:** complete

### Phase 11: PR 5 Prompt Compiler
- [x] Add backend `/api/prompts/compile` route.
- [x] Add Prompt Compiler request/response models.
- [x] Add tag extraction, model optimizers, scorer, OpenAI LLM provider, and rule fallback provider.
- [x] Add frontend normal/professional mode controls.
- [x] Add frontend GPT Image/NovelAI target model controls.
- [x] Add candidate prompt display and local selection state.
- [x] Add backend runtime LLM config API.
- [x] Add frontend LLM config page.
- [x] Add PR 5 description document.
- **Status:** complete

### Phase 12: PR 5 Verification
- [x] Run backend tests.
- [x] Run frontend tests.
- [x] Run frontend production build.
- [x] Verify frontend dev HTML is served locally.
- [ ] Push PR 5 branch.
- **Status:** in_progress

## Key Questions
1. Which backend stack? Answered: Python FastAPI.
2. How many PRs? Answered: 12 clear PRs.

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| FastAPI backend | Fast for AI/file/image workflows and easy API docs. |
| React + Vite frontend | Lightweight and matches the plan. |
| JSON file repository | MVP-friendly and inspectable. |
| Mock provider creates fallback PNGs | Keeps demo runnable without checked-in binary assets or API keys. |
| Simulated cloud upload when Qiniu keys are missing | Keeps acceptance flow demonstrable. |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Git safe.directory and config permission issues | 1 | Used approved `git -c safe.directory=...` earlier for Git reads/config. |
| PowerShell background Uvicorn launch did not persist reliably | 1 | Verified app with pytest/TestClient and foreground Uvicorn startup; use foreground command for manual API checks. |

## Notes
- Avoid relying on real AI image APIs for MVP acceptance.
- Keep generated runtime files under `storage/`.
