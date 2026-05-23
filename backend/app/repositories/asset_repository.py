import json
from pathlib import Path

from app.models.asset_models import AssetRecord

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = BACKEND_ROOT / "runtime" / "storage" / "asset-db.json"


class AssetRepository:
    def save_generation(self, generation_id: str, assets: list[AssetRecord]) -> None:
        data = self._load()
        data["generations"][generation_id] = {
            "generationId": generation_id,
            "assetIds": [asset.id for asset in assets],
        }
        for asset in assets:
            data["assets"][asset.id] = asset.model_dump()
        self._save(data)

    def list_assets(self) -> list[AssetRecord]:
        data = self._load()
        return [AssetRecord(**asset) for asset in data["assets"].values()]

    def _load(self) -> dict:
        if not DB_PATH.exists():
            return {"generations": {}, "assets": {}}
        return json.loads(DB_PATH.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
