# import requests
# import json
# from typing import List, Dict

# def get_instruments_from_openapi(url: str, tokens: List[str]) -> List[Dict]:
#     try:
#         print(url, "url")
#         response = requests.get(url)
#         print(response, "response")
#         response.raise_for_status()
#         data = response.json()
#         print(data, "data")
#         print("Tokens to match:", tokens)
#         filtered = [
#             item for item in data
#             if item.get("exch_seg") == "NFO" and item.get("symbol") in tokens
#         ]
#         print(filtered, "filtered")
#         return filtered

#     except Exception as e:
#         print(f"[ERROR] Failed to fetch instruments from {url}: {e}")
#         return []
import requests
import json
from typing import List, Dict

def get_instruments_from_openapi(url: str, tokens: List[str]) -> List[Dict]:
    try:
        print("URL:", url)
        response = requests.get(url)
        print("Response Status:", response.status_code)

        response.raise_for_status()
        data = response.json()
        print(f"Total instruments received: {len(data)}")

        # Normalize tokens (strip spaces, uppercase)
        normalized_tokens = [t.strip().upper() for t in tokens]
        print("Tokens to match (normalized):", normalized_tokens)

        filtered = []
        for item in data:
            exch_seg = item.get("exch_seg", "").strip().upper()
            symbol = item.get("symbol", "").strip().upper()

            if exch_seg == "NFO" and symbol in normalized_tokens:
                filtered.append(item)

        print(f"Filtered count: {len(filtered)}")
        if not filtered:
            print("⚠️ No matches found. Debug sample symbols from API:")
            print([d.get("symbol") for d in data[:20]])  # print first 20 for debugging

        return filtered

    except Exception as e:
        print(f"[ERROR] Failed to fetch instruments from {url}: {e}")
        return []
