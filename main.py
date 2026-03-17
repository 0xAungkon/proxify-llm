from fastapi import FastAPI
import uvicorn
from config.settings import settings
from inc.LogHelpers import configure_logger, logger
from routers.health import router as health_router
from routers.common import router as common_router
from routers.proxy import router as proxy_router

configure_logger(settings.log_folder, settings.log_retention_days)
logger.info("Logger configured")

app = FastAPI()
app.include_router(health_router)
app.include_router(common_router)
app.include_router(proxy_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.proxy_host, port=settings.proxy_port, reload=True)