import yt_dlp
from prefect import task
from concurrent.futures import ThreadPoolExecutor

def get_video_metadata(video_url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,       # Don't fetch media
        'extract_flat': True,        # Only metadata
        'noplaylist': True,          # Avoid full playlist crawling
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            metadata = {
                'title': info_dict.get('title'),
                'description': info_dict.get('description'),
                'published_at': info_dict.get('upload_date'),
                'view_count': info_dict.get('view_count'),
                'like_count': info_dict.get('like_count', 'N/A'),
                'duration': info_dict.get('duration'),
                'youtube_url': video_url,
            }
            return metadata
    except Exception as e:
        return {'youtube_url': video_url, 'error': str(e)}

@task
def fetch_youtube_multiple_metadata(urls):
    # Use all CPU cores for parallel fetching
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(get_video_metadata, urls))
    return results