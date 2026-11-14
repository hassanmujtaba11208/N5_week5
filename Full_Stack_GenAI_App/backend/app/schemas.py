from pydantic import BaseModel, Field, field_validator
from typing import Literal, Any

class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    mode: Literal["rag", "agent"] = "rag"
    top_k: int = Field(default=3, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, value: str):
        if not value.strip():
            raise ValueError("query cannot be blank")
        return value.strip()

class AskResponse(BaseModel):
    mode: str
    answer: str
    results: list[dict[str, Any]] = Field(default_factory=list)
    tool_used: str | None = None
    iterations: int = 0
    request_id: str
