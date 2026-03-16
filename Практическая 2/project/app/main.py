import uvicorn
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import settings
from contextlib import asynccontextmanager

from models import db_helper, Base
from api import router as api_router
from routers.test_routes import router as test_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    # async with db_helper.engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield
    # shutdown
    await db_helper.dispose()


main_app = FastAPI(
    lifespan=lifespan,
)
app_dir = Path(__file__).resolve().parent
static_dir = app_dir / "static"
uploads_dir = static_dir / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
main_app.mount("/static", StaticFiles(directory=static_dir), name="static")

main_app.include_router(
    api_router,
)
main_app.include_router(test_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.reload,
    )
