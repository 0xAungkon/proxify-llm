from pydantic import BaseModel, field_validator

class LLMProviderSchema(BaseModel):
    base_url: str
    api_key: str
    vendor: str

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        if not v:
            raise ValueError("base_url cannot be empty")
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        return v.strip()
    
    @field_validator("vendor")
    @classmethod
    def validate_vendor(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("vendor cannot be empty")
        return v.strip()