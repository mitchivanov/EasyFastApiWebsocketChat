from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.router_page import router as router_page
from app.api.router_socket import router as router_socket
from app.database import init_db
from contextlib import asynccontextmanager
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализируем базу данных при запуске
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.mount('/static', StaticFiles(directory='app/static'), 'static')
app.include_router(router_socket)
app.include_router(router_page)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        ws="websockets",
        log_level="debug"
    )