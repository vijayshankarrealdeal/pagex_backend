import yt_dlp
from concurrent.futures import ThreadPoolExecutor

def get_video_metadata(video_url):
    ydl_opts = {
        'quiet': True,  # Suppress output
        'force_generic_extractor': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        metadata = {
            'title': info_dict.get('title', None),
            'description': info_dict.get('description', None),
            'published_at': info_dict.get('upload_date', None),
            'view_count': info_dict.get('view_count', None),
            'like_count': info_dict.get('like_count', 'N/A'),
            'duration': info_dict.get('duration', None),
            'url': info_dict.get('url', None),
        }
        return metadata

def fetch_multiple_metadata(urls):
    # Using ThreadPoolExecutor to fetch metadata in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(get_video_metadata, urls)
    return list(results)

def get_metadata_payload():
    ## use llm to get metadata as formated payload
    pass