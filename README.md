# GameAsset Forge

GameAsset Forge is an AI 2D game asset production and delivery platform for indie game developers. It turns natural-language game requirements into structured image prompts, generates asset files through a provider layer, checks asset quality, organizes an asset library, exports `manifest.json` and zip packages, and supports cloud delivery through Qiniu or a local simulated upload mode.

This repository is organized to implement the MVP with:

- Frontend: React + Vite
- Backend: Python + FastAPI
- Storage: local JSON file and generated files under `storage/`
- Image pipeline: Mock Provider by default
- Export: `manifest.json` + zip package
- Cloud delivery: simulated upload when Qiniu keys are not configured

## Core Flow

```text
Input request -> Prompt Compiler -> Image Provider -> Quality Inspector -> Asset Library -> Cloud Upload -> zip + manifest Export
```

## Local Setup

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend URL printed by Vite. The backend API runs at `http://127.0.0.1:8000` by default.

> Current stage: PR 1 project bootstrap. Runtime code lands in later PRs according to `docs/PR_PLAN.md`.

## Mock Mode

Mock mode is enabled by default:

```env
IMAGE_PROVIDER=mock
```

The Mock Provider does not call any external image API. It creates or reuses local placeholder PNG files, then still runs the full production pipeline: prompt compilation, file generation, persistence, quality scoring, upload status, manifest generation, and zip export.

## API Overview

- `GET /api/health`
- `POST /api/assets/generate`
- `GET /api/assets`
- `GET /api/assets/{asset_id}/quality`
- `POST /api/assets/{asset_id}/upload`
- `POST /api/exports/{generation_id}`

## Original Engineering Features

1. Prompt Compiler: compiles user intent and asset metadata into structured 2D game asset prompts.
2. Asset Quality Inspector: scores generated assets by file format, dimensions, naming, category placement, prompt records, manifest status, and upload status.
3. Cloud Asset Hub: stores upload state and provides simulated or real cloud preview URLs for asset delivery.

## PR Plan

See [docs/PR_PLAN.md](docs/PR_PLAN.md).

## Demo Script

See [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

## Third-Party Dependencies

Backend dependencies are listed in `backend/requirements.txt`. Frontend dependencies are listed in `frontend/package.json`.

## Current Acceptance Checklist

- [ ] Mock mode can run without API keys.
- [ ] Prompt Compiler is implemented.
- [ ] Mock Provider is implemented.
- [ ] Asset library API is implemented.
- [ ] Quality report API is implemented.
- [ ] manifest and zip export are implemented.
- [ ] Simulated cloud upload is implemented.
- [ ] Demo video link added.
- [ ] Final screenshots added.
