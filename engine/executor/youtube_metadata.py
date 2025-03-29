from typing import List
import yt_dlp
from prefect import task
from concurrent.futures import ThreadPoolExecutor

from engine.models.youtube_payload import YoutubePayload


def get_video_metadata(video_url) -> YoutubePayload:
    ydl_opts = {
        "quiet": True,
        "skip_download": True,  # Don't fetch media
        "extract_flat": True,  # Only metadata
        "noplaylist": True,  # Avoid full playlist crawling
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            metadata = {
                "title": info_dict.get("title"),
                "summary": info_dict.get("description"),
                "url": video_url,
                "result_rank": 0,
                "video_details": {
                    "channel": info_dict.get("uploader"),
                    "air_time": info_dict.get("upload_date"),
                    "duration_seconds": info_dict.get("duration"),
                    "published_at": info_dict.get("upload_date"),
                },
                "like_count": info_dict.get("like_count", "N/A"),
                "view_count": info_dict.get("view_count"),
                "is_youtube": True,
            }
            return YoutubePayload(**metadata)
    except Exception as e:
        return {"youtube_url": video_url, "error": str(e)}


@task
def fetch_youtube_multiple_metadata(urls) -> List[YoutubePayload]:
    # Use all CPU cores for parallel fetching
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(get_video_metadata, urls))
    return results
