from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any


class URLModel(BaseModel):
    url : str
    title : Optional[str] = Field(None, description="Title of the URL")
    description : Optional[str] = Field(None, description="Description of the URL")
    result_rank : Optional[int] = Field(None, description="Rank of the URL based on relevance")

class URLResponseModel(BaseModel):
    urls: List[URLModel] = Field(..., description="List of URLs")

