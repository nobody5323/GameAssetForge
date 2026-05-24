# Task Plan: Implement GameAsset Forge MVP

## Goal
Build a runnable GameAsset Forge MVP matching the 12-PR plan: React/Vite frontend, FastAPI backend, mock asset generation, quality inspection, manifest/zip export, simulated cloud upload, and documentation.

## Current Phase
PR 12 — MVP Complete

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
- [x] Push PR 5 branch.
- **Status:** complete

### Phase 13: PR 6 Mock Image Provider
- [x] Create `feature/pr-06-mock-image-provider` from latest `origin/main`.
- [x] Add image provider request/response models.
- [x] Add `ImageProvider.generate()` interface.
- [x] Add `MockImageProvider`.
- [x] Add standard-library PNG writer for runtime mock assets.
- [x] Add unit tests for generated paths, metadata, seed reuse, and unknown asset types.
- [x] Add PR 6 description document.
- **Status:** complete

### Phase 14: PR 6 Verification
- [x] Run backend tests.
- [x] Push PR 6 branch.
- **Status:** complete

### Phase 15: PR 7 Asset Generation Service
- [x] Create `feature/pr-07-asset-generation-service` from latest `origin/main`.
- [x] Add `POST /api/assets/generate`.
- [x] Add `AssetGenerationService`.
- [x] Add JSON-backed `AssetRepository`.
- [x] Persist generated asset records.
- [x] Connect frontend `GENERATE ASSETS` to the backend API.
- [x] Display generation id, local asset path, provider, and prompt hash.
- [x] Add PR 7 description document.
- **Status:** complete

### Phase 17: PR 8 Asset Library
- [x] Create `feature/pr-08-asset-library` from latest `origin/main`.
- [x] Add `GET /api/assets?category=` route with optional category filter.
- [x] Add `fetchAssets()` frontend API helper.
- [x] Rewrite LibraryPage with dynamic data, filter chips, image thumbnails, and loading/empty/error states.
- [x] Add filter chip and library panel CSS.
- [x] Add backend tests for list, filter, empty category, and field completeness.
- [x] Add frontend test for fetchAssets export.
- [x] Add PR 8 description document.
- **Status:** complete

### Phase 19: PR 9 Quality Inspector
- [x] Create `feature/pr-09-quality-inspector` from latest `origin/main`.
- [x] Add `QualityCheck`, `AssetQualityReport`, `GenerationQualityReport` Pydantic models.
- [x] Implement `QualityService` with 7 checks: format, dimensions, naming, category, prompt, manifest, cloud readiness.
- [x] Implement PNG IHDR parser using standard library `struct`.
- [x] Add `POST /api/quality/inspect/{asset_id}` endpoint.
- [x] Add `GET /api/quality/report/{generation_id}` endpoint.
- [x] Register quality router in `main.py`.
- [x] Add 11 tests covering all checks, scoring, API endpoints, edge cases.
- [x] Add PR 9 description document.
- **Status:** complete

### Phase 21: PR 10 Quality Report Page
- [x] Create `feature/pr-10-quality-report-page` from latest `origin/main`.
- [x] Add `fetchQualityReport()` frontend API helper.
- [x] Rewrite `QualityPage` with generation selector, overall score ring, per-asset check breakdown.
- [x] Add quality report CSS: score ring, stats cards, check rows with pass/fail coloring.
- [x] Add frontend test for `fetchQualityReport`.
- [x] Add PR 10 description document.
- **Status:** complete

### Phase 22: PR 10 Verification
- [x] Backend 34 tests passed.
- [x] Frontend 15 tests passed.
- [x] Frontend build succeeded.
- **Status:** complete

### Phase 21: PR 10 Quality Report Page
- [x] Create `feature/pr-10-quality-report-page` from latest `origin/main`.
- [x] Add `fetchQualityReport()` frontend API helper.
- [x] Rewrite QualityPage with score ring, check breakdown, generation selector.
- [x] Add quality report CSS (score ring, pass/fail stats, check rows).
- [x] Add frontend test for fetchQualityReport.
- [x] Add PR 10 description document.
- **Status:** complete

### Phase 22: PR 10 Verification
- [x] Run frontend tests and build.
- **Status:** complete

### Phase 23: PR 11 Manifest & Zip Export
- [x] Create `feature/pr-11-manifest-and-zip-export` from latest `origin/main`.
- [x] Add `Manifest`, `ManifestAsset`, `ExportResponse` Pydantic models.
- [x] Implement `ExportService` with manifest generation, zip packaging, quality score integration.
- [x] Add `POST /api/exports/{generation_id}` zip download endpoint.
- [x] Add `GET /api/exports` generation list endpoint.
- [x] Add `projectName` to AssetRecord and persist in generation service.
- [x] Register export router in `main.py`.
- [x] Add 8 backend tests covering zip validity, manifest content, API endpoints, edge cases.
- [x] Add `fetchExportableGenerations()` and `exportGeneration()` frontend API helpers.
- [x] Rewrite ExportPage with generation selector, download trigger, result card.
- [x] Add export page CSS styles.
- [x] Add PR 11 description document.
- **Status:** complete

### Phase 24: PR 11 Verification
- [x] Run backend tests (42 passed).
- [x] Run frontend tests (16 passed).
- [x] Run frontend production build.
- **Status:** complete

### Phase 25: PR 12 Cloud Simulation & Final Docs
- [x] Create `feature/pr-12-cloud-and-demo-docs` from latest `origin/main`.
- [x] Merge PR11 into PR12 for complete codebase.
- [x] Add `CloudProvider` abstract interface and `CloudUploadResult`.
- [x] Add `MockCloudProvider` with `cloud://mock/...` simulated URLs.
- [x] Add `CloudService` to orchestrate upload and update AssetRecord.cloudUrl.
- [x] Add `POST /api/cloud/upload/{asset_id}` and `POST /api/cloud/upload-generation/{generation_id}`.
- [x] Add `update_asset()` and `find_asset()` to AssetRepository.
- [x] Register cloud router in `main.py`.
- [x] Add 7 backend tests covering upload, cloudUrl, API, 404.
- [x] Add `uploadAssetToCloud()` and `uploadGenerationToCloud()` frontend helpers.
- [x] Add cloud upload section to ExportPage with upload button and result display.
- [x] Rewrite README.md: full tech stack, API table, Quick Start, project structure, acceptance checklist.
- [x] Update DEMO_SCRIPT.md: 6-segment walkthrough.
- [x] Add PR 12 description document.
- **Status:** complete

### Phase 26: PR 12 Verification
- [x] Run backend tests (49 passed).
- [x] Run frontend tests (17 passed).
- [x] Run frontend production build.
- **Status:** complete

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
