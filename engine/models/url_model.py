from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ImagePayload(BaseModel):
    src: str
    alt: str
class PageContent(BaseModel):
    images: List[ImagePayload]
    full_text: str

class BasePayload(BaseModel):
    url : str
    title : Optional[str] = Field(None, description="Title of the URL")
    summary : Optional[str] = Field(None, description="Description of the URL")
    short_description : Optional[str] = Field(None, description="Short description of the URL content")
    result_rank : Optional[int] = Field(None, description="Rank of the URL based on relevance")
    rank_reason: Optional[str] = Field(None, description="Reason for the rank")
    is_youtube : Optional[bool] = Field(None, description="Is the URL a YouTube link")

class URLResponseModel(BaseModel):
    page_content : Optional[PageContent] = Field(None, description="Content of the Main URL")
    urls: Optional[List[BasePayload]] = Field(..., description="List of URLs")
