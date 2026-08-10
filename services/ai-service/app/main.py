from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.itinerary import router as itinerary_router
from app.api.routes.place_suggestions import router as place_suggestions_router
from app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router, prefix="/internal/v1")
    application.include_router(chat_router, prefix="/internal/v1")
    application.include_router(itinerary_router, prefix="/internal/v1")
    application.include_router(place_suggestions_router, prefix="/internal/v1")
    return application


app = create_app()
