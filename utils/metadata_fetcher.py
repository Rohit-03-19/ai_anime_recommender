import requests

def fetch_anime_details(title):
    """Fetches poster, rating, and MAL link from Jikan API."""
    try:
        url = f"https://api.jikan.moe/v4/anime?q={title}&limit=1"
        response = requests.get(url).json()
        if response['data']:
            anime = response['data'][0]
            return {
                "image": anime['images']['jpg']['large_image_url'],
                "rating": anime['score'],
                "url": anime['url'], # MyAnimeList link
                "title": anime['title_english'] or anime['title']
            }
    except Exception as e:
        print(f"Error fetching {title}: {e}")
    return None