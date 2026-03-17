from fastapi import APIRouter, Request

from services.ProxyService import handle_proxy_request
from schema.LLMProviderSchema import LLMProviderSchema
from config.settings import settings

router = APIRouter()


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    return await handle_proxy_request(path=path, request=request)

@router.api_route("/health", methods=["GET"])
async def health_check():
    return {"status": "ok"}

@router.api_route("/generate-api", methods=["POST"])
async def generate_api(llm_provider: LLMProviderSchema):
    return {"api_token": llm_provider.api_key}