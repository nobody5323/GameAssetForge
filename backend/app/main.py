from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes.asset_routes import router as asset_router
from app.routes.config_routes import router as config_router
from app.routes.health_routes import router as health_router
from app.routes.prompt_routes import router as prompt_router


def create_app() -> FastAPI:
    runtime_dir = Path(__file__).resolve().parents[1] / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(
        title="GameAsset Forge API",
        description="Backend API shell for the GameAsset Forge asset pipeline.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:4173",
            "http://localhost:4173",
            "http://127.0.0.1:4174",
            "http://localhost:4174",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(prompt_router, prefix="/api")
    app.include_router(config_router, prefix="/api")
    app.include_router(asset_router, prefix="/api")
    app.mount("/runtime", StaticFiles(directory=runtime_dir), name="runtime")
    return app


app = create_app()
