from pydantic import BaseModel
from datetime import datetime
from pydantic import field_validator

from engine.models.url_model import BasePayload


class VideoDetails(BaseModel):
    channel: str
    duration_seconds: int
    published_at: datetime

    @field_validator("published_at", mode="before")
    def parse_published_at(cls, value):
        return datetime.strptime(value, "%Y%m%d")

class YoutubePayload(BasePayload):
    view_count: int
    like_count: int
    video_details: dict