from pydantic import BaseModel, Field


class ShortLivedPasswordRequest(BaseModel):
    token_type: str = Field("password")
    service: str = Field("DPA-DB")
