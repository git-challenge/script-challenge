import logging
import os
from typing import Dict, List, Any
import requests
from src.utils import get_env_int, bounded_sleep


API_BASE = os.getenv("API_URL")
HTTP_TIMEOUT = get_env_int("HTTP_TIMEOUT", 20)         
MAX_RETRIES  = get_env_int("MAX_RETRIES", 4)          
BACKOFF_BASE = float(os.getenv("BACKOFF_BASE", 0.8))
BACKOFF_CAP  = float(os.getenv("BACKOFF_CAP", 8))     

def _request_with_backoff(method: str, url: str, **kwargs) -> requests.Response:
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.request(method, url, timeout=HTTP_TIMEOUT, **kwargs)
            
            if resp.status_code in (429, 503):
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait_s = min(float(retry_after), BACKOFF_CAP)
                    except ValueError:
                        wait_s = min((BACKOFF_BASE ** attempt) * 2, BACKOFF_CAP)
                else:
                    wait_s = min((BACKOFF_BASE ** attempt) * 2, BACKOFF_CAP)
                logging.warning(f"HTTP {resp.status_code}. Waiting {wait_s:.2f}s (Retry-After) and retrying...")
                bounded_sleep(wait_s)
                continue

            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            if attempt >= MAX_RETRIES:
                logging.error(f"HTTP error after {attempt} retries: {e}")
                raise
            
            wait_s = min((BACKOFF_BASE ** (attempt + 1)) * 2, BACKOFF_CAP)
            logging.warning(f"Request failure: {e}. Backing off {wait_s:.2f}s (attempt {attempt+1}/{MAX_RETRIES})")
            bounded_sleep(wait_s)
    
    raise RuntimeError("Unreachable: backoff loop exited unexpectedly")

def _search_ids(term: str, max_items: int) -> List[str]:
    ids: List[str] = []
    page = 1
    per_page = min(max(1, max_items), 100)  
    
    while len(ids) < max_items:
        url = f"{API_BASE}/search"
        params = {"q": term, "page": page, "limit": per_page}
        resp = _request_with_backoff("GET", url, params=params)
        payload = resp.json()
        data = payload.get("data", [])
        
        if not data:
            break
        
        ids.extend(str(item["id"]) for item in data if "id" in item)
        page += 1
    
    return ids[:max_items]

def _chunk(lst: List[str], size: int) -> List[List[str]]:
    return [lst[i:i + size] for i in range(0, len(lst), size)]

def _fetch_details(ids: List[str], fields: List[str]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not ids:
        return results
    
    fields_csv = ",".join(fields) if fields else "id,title,artist_title,date_display"
    
    for batch in _chunk(ids, 50):
        url = f"{API_BASE}"
        params = {"ids": ",".join(batch), "fields": fields_csv}
        resp = _request_with_backoff("GET", url, params=params)
        payload = resp.json()
        results.extend(payload.get("data", []))
    
    return results

def fetch_report_data(report: Dict[str, Any]) -> Dict[str, Any]:
    name = report.get("name") or "report"
    search = report.get("search") or ""
    fields = report.get("fields") or ["id", "title", "artist_title", "date_display"]
    max_items = int(report.get("max_items") or 25)

    logging.info(f"[{name}] Fetch start | search='{search}' | fields={fields} | max_items={max_items}")

    ids = _search_ids(search, max_items)
    logging.info(f"[{name}] search found {len(ids)} ids")

    items = _fetch_details(ids, fields)
    logging.info(f"[{name}] fetched {len(items)} details")

    return {
        "report": {
            "name": name,
            "search": search,
            "fields": fields,
            "max_items": max_items
        },
        "items": items,
        "count": len(items)
    }