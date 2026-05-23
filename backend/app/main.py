from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.health_routes import router as health_router


def create_app() -> FastAPI:
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
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api", tags=["health"])
    return app


app = create_app()
