from fastapi import APIRouter, Request

from inc.TokenManager import encrypt_token
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

@router.api_route("/generate-api-token", methods=["POST"])
async def generate_api_token(llm_provider: LLMProviderSchema):
    data = {
        "base_url": llm_provider.base_url,
        "api_key": llm_provider.api_key,
        "vendor": llm_provider.vendor
    }

    encrypted_token = encrypt_token(str(data))
    return {"api_token": encrypted_token}