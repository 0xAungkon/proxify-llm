from fastapi import APIRouter, Request

from services.ProxyService import handle_proxy_request

router = APIRouter(tags=["Proxy"])


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    return await handle_proxy_request(path=path, request=request)