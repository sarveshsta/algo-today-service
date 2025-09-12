import requests
import json
from typing import List, Dict

def get_instruments_from_openapi(url: str, tokens: List[str]) -> List[Dict]:
    try:
        print(url, "url")
        response = requests.get(url)
        print(response, "response")
        response.raise_for_status()
        data = response.json()
        print(data, "data")
        print("Tokens to match:", tokens)
        filtered = [
            item for item in data
            if item.get("exch_seg") == "NFO" and item.get("symbol") in tokens
        ]
        print(filtered, "filtered")
        return filtered

    except Exception as e:
        print(f"[ERROR] Failed to fetch instruments from {url}: {e}")
        return []
