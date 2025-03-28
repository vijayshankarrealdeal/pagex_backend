from pydantic import BaseModel
from datetime import datetime
from pydantic import field_validator


class VideoDetails(BaseModel):
    channel: str
    duration_seconds: int
    published_at: datetime

    @field_validator("published_at", mode="before")
    def parse_published_at(cls, value):
        return datetime.strptime(value, "%Y%m%d")

class YoutubePayload(BaseModel):
    title: str
    summary: str
    view_count: int
    like_count: int
    video_details: dict



test_payload={
  "title": "Trump's 25% Auto Tariff: Global Backlash and India's Concerns",
  "summary": "In this live broadcast of 'Vantage with Palki Sharma' by Firstpost, US President Donald Trump announces a new policy imposing a 25% tariff on imported cars and light trucks, set to take effect next week. Trump argues that the move will boost domestic growth by encouraging companies to relocate production back to the United States, countering previous trends of offshoring to Mexico and Canada. The announcement has sparked significant international backlash—the European Union condemned the decision, and Canadian Prime Minister Mark Carney called it a 'direct attack' on Canadian workers. The program also examines the potential impact of the tariffs on India, offering insights from an Indian perspective on global trade dynamics.",
  "view_count": 55453,
  "like_count": 1281,
  "video_details": {
    "channel": "Firstpost",
    "air_time": "9 PM IST (Monday to Friday)",
    "duration_seconds": 3920,
    "published_at": "20250327"
  }
}

x = YoutubePayload(**test_payload)
print(x)