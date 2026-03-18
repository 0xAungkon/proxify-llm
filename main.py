from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import argparse
import atexit
import signal
import sys
from config.settings import settings
from inc.LogHelpers import configure_logger, logger
from inc.TunnelHepler import PinggyHelper
from routers.admin import router as admin_router
from routers.health import router as health_router
from routers.common import router as common_router
from routers.proxy import router as proxy_router

configure_logger(settings.log_folder, settings.log_retention_days)
logger.info("Logger configured")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(health_router)
app.include_router(common_router)
app.include_router(admin_router)
app.include_router(proxy_router)

# Global tunnel helper
tunnel_helper = None


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Proxify LLM Proxy Server")
    parser.add_argument(
        "--tunnel",
        choices=["pinggy"],
        help="Enable tunnel (e.g., pinggy for Pinggy SSH tunnel)"
    )
    parser.add_argument(
        "--tunnel-token",
        default=None,
        help="Custom tunnel token/host (e.g., user@host.pinggy.io). If not provided, uses qr@free.pinggy.io"
    )
    return parser.parse_args()


def cleanup_tunnel():
    """Clean up tunnel on exit."""
    global tunnel_helper
    if tunnel_helper:
        logger.info("Cleaning up tunnel...")
        tunnel_helper.stop_tunnel()


if __name__ == "__main__":
    args = parse_arguments()
    
    # Register cleanup handler
    atexit.register(cleanup_tunnel)
    signal.signal(signal.SIGINT, lambda sig, frame: (cleanup_tunnel(), sys.exit(0)))
    
    # Initialize tunnel if requested
    if args.tunnel == "pinggy":
        tunnel_helper = PinggyHelper(args.tunnel_token or "qr@free.pinggy.io")
        tunnel_helper.start_tunnel(
            local_port=settings.proxy_port,
            tunnel_token=args.tunnel_token
        )
    
    uvicorn.run("main:app", host=settings.proxy_host, port=settings.proxy_port, reload=True)