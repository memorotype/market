import os
import requests

def fetch_google_image(query: str) -> str | None:
    key = os.environ.get("GOOGLE_CSE_KEY")
    cx  = os.environ.get("GOOGLE_CSE_CX")
    if not key or not cx:
        return None
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "searchType": "image",
        "num": 1,
        "safe": "active",
        "key": key,
        "cx": cx
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("items", [{}])[0].get("link")
    except Exception:
        return None
