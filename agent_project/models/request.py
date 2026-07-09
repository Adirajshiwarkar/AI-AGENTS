from pydantic import BaseModel, Field, field_validator

class AgentRequest(BaseModel):
    request: str = Field(..., description="The natural language request for generating a business document.")

    @field_validator("request")
    @classmethod
    def validate_request_content(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Request must not be empty or blank.")
        if len(stripped) < 10:
            raise ValueError("Request is too short. Please provide a more descriptive prompt (minimum 10 characters).")
        return stripped
