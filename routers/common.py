from fastapi import APIRouter

from inc.TokenManager import encrypt_token
from schema.LLMProviderSchema import LLMProviderSchema

router = APIRouter(tags=["Common"])


@router.post("/generate-api-token")
async def generate_api_token(llm_provider: LLMProviderSchema):
    data = {
        "base_url": llm_provider.base_url,
        "api_key": llm_provider.api_key,
        "vendor": llm_provider.vendor,
    }
    encrypted_token = encrypt_token(str(data))
    return {"api_token": encrypted_token}
