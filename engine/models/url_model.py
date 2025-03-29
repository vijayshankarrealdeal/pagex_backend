from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any


class BasePayload(BaseModel):
    url : str
    title : Optional[str] = Field(None, description="Title of the URL")
    summary : Optional[str] = Field(None, description="Description of the URL")
    result_rank : Optional[int] = Field(None, description="Rank of the URL based on relevance")
    rank_reason: Optional[str] = Field(None, description="Reason for the rank")
    is_youtube : Optional[bool] = Field(None, description="Is the URL a YouTube link")

class URLResponseModel(BaseModel):
    urls: List[BasePayload] = Field(..., description="List of URLs")

