# Project Engineering Notes

The original engineering design document is preserved in the repository root as `GameAssetForge工程设计文档(1) (1).md`.

This MVP follows its recommended core chain:

```text
Input -> Prompt Compiler -> Image Provider -> Quality Inspector -> Cloud Asset Hub -> Export
```

Implementation defaults:

- FastAPI backend under `backend/app`
- React/Vite frontend under `frontend`
- Local JSON persistence at `storage/db.json`
- Runtime generated assets under `storage/generated-assets`
- Runtime exports under `storage/exports`
