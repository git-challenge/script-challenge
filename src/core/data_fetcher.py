import os
import logging
import requests
from dotenv import load_dotenv


load_dotenv()

def fetch_artworks(search, fields, limit):
    BASE_URL = os.getenv("API_URL")
    BASE_SEARCH_URL = f"{BASE_URL}/search"

    logging.info(f"Fetching artworks from API | search='{search}' | fields={fields} | limit={limit}")

    try:
        search_params = {"q": search, "limit": limit}
        search_resp = requests.get(BASE_SEARCH_URL, params=search_params)
        search_resp.raise_for_status()
        search_data = search_resp.json()

        ids = [str(item["id"]) for item in search_data.get("data", [])]
        if not ids:
            logging.warning("No artworks found for the given search term.")
            return []

        fields_str = ",".join(fields)
        detail_params = {"ids": ",".join(ids), "fields": fields_str}
        detail_resp = requests.get(BASE_URL, params=detail_params)
        detail_resp.raise_for_status()
        detail_data = detail_resp.json()

        logging.info(f"Retrieved {len(detail_data.get('data', []))} artworks.")
        return detail_data.get("data", [])

    except requests.RequestException as e:
        logging.error(f"Error fetching artworks: {e}")
        return []