import os
import requests

def fetch_google_image(query: str) -> str | None:
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        return None

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": query,
        "tbm": "isch",   # Google Images
        "api_key": key
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        images = data.get("images_results", [])
        if images:
            return images[0].get("original")
        return None
    except Exception:
        return None
