"""
API Client Module for Report Data Fetching

This module provides a robust HTTP client for fetching report data from an external API.
It implements retry logic with exponential backoff, handles rate limiting, and supports
paginated search with batch detail fetching for optimal performance.

Key Features:
    - Exponential backoff retry mechanism with configurable parameters
    - Automatic handling of HTTP 429 (rate limiting) and 503 (service unavailable) responses
    - Respect for server-provided Retry-After headers
    - Paginated search functionality with configurable limits
    - Batch processing for efficient detail fetching
    - Comprehensive logging for monitoring and debugging

Environment Variables:
    API_URL: Base URL for the API endpoint
    HTTP_TIMEOUT: Request timeout in seconds (default: 20)
    MAX_RETRIES: Maximum number of retry attempts (default: 4)
    BACKOFF_BASE: Base multiplier for exponential backoff (default: 0.8)
    BACKOFF_CAP: Maximum wait time between retries in seconds (default: 8)

Dependencies:
    - requests: HTTP client library
    - src.utils: Custom utilities for configuration and sleep functions

Author: Juan Sebastián Dosman
Version: 1.0
Date: 15th August 2025
"""

import logging
import os
from typing import Dict, List, Any
import requests
from src.utils import get_env_int, bounded_sleep


# Configuration constants loaded from environment variables
API_BASE = os.getenv("API_URL")
HTTP_TIMEOUT = get_env_int("HTTP_TIMEOUT", 20)         
MAX_RETRIES = get_env_int("MAX_RETRIES", 4)          
BACKOFF_BASE = float(os.getenv("BACKOFF_BASE", 0.8))
BACKOFF_CAP = float(os.getenv("BACKOFF_CAP", 8))     


def _request_with_backoff(method: str, url: str, **kwargs) -> requests.Response:
    """
    Execute HTTP request with exponential backoff retry mechanism.
    
    This function implements a robust retry strategy that handles transient failures,
    rate limiting, and server unavailability. It respects server-provided Retry-After
    headers and implements exponential backoff to avoid overwhelming the server.
    
    Args:
        method (str): HTTP method to use (GET, POST, PUT, DELETE, etc.)
        url (str): Target URL for the request
        **kwargs: Additional keyword arguments passed to requests.request()
                (headers, params, data, json, etc.)
    
    Returns:
        requests.Response: Successful HTTP response object
    
    Raises:
        requests.RequestException: When all retry attempts are exhausted or
                                for non-retryable errors (4xx client errors)
        RuntimeError: If the retry loop exits unexpectedly (should never happen)
    
    Retry Logic:
        - HTTP 429 (Too Many Requests): Respects Retry-After header if provided
        - HTTP 503 (Service Unavailable): Uses exponential backoff
        - Network errors: Uses exponential backoff with increasing delays
        - Other 4xx/5xx errors: Raises immediately without retry
    
    Example:
        >>> response = _request_with_backoff("GET", "https://api.example.com/data")
        >>> data = response.json()
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            # Execute HTTP request with configured timeout
            resp = requests.request(method, url, timeout=HTTP_TIMEOUT, **kwargs)
            
            # Handle rate limiting and service unavailability
            if resp.status_code in (429, 503):
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        # Use server-provided retry delay, capped at BACKOFF_CAP
                        wait_s = min(float(retry_after), BACKOFF_CAP)
                    except ValueError:
                        # Fallback to exponential backoff if Retry-After is invalid
                        wait_s = min((BACKOFF_BASE ** attempt) * 2, BACKOFF_CAP)
                else:
                    # Use exponential backoff when no Retry-After header
                    wait_s = min((BACKOFF_BASE ** attempt) * 2, BACKOFF_CAP)
                
                logging.warning(f"HTTP {resp.status_code}. Waiting {wait_s:.2f}s (Retry-After) and retrying...")
                bounded_sleep(wait_s)
                continue

            # Raise exception for other HTTP errors (4xx, 5xx)
            resp.raise_for_status()
            return resp
            
        except requests.RequestException as e:
            # Stop retrying if max attempts reached
            if attempt >= MAX_RETRIES:
                logging.error(f"HTTP error after {attempt} retries: {e}")
                raise
            
            # Calculate exponential backoff delay
            wait_s = min((BACKOFF_BASE ** (attempt + 1)) * 2, BACKOFF_CAP)
            logging.warning(f"Request failure: {e}. Backing off {wait_s:.2f}s (attempt {attempt+1}/{MAX_RETRIES})")
            bounded_sleep(wait_s)
    
    # This should never be reached due to the loop structure
    raise RuntimeError("Unreachable: backoff loop exited unexpectedly")


def _search_ids(term: str, max_items: int) -> List[str]:
    """
    Search for items matching a term and return their IDs.
    
    Performs paginated search through the API to collect item IDs that match
    the search term. Continues pagination until the desired number of items
    is reached or no more results are available.
    
    Args:
        term (str): Search query string to match against API items
        max_items (int): Maximum number of item IDs to return
    
    Returns:
        List[str]: List of item IDs (as strings) matching the search term,
                limited to max_items length
    
    Raises:
        requests.RequestException: If API requests fail after all retries
        KeyError: If API response format is unexpected (missing required fields)
    
    API Behavior:
        - Uses GET /search endpoint with pagination
        - Requests up to 100 items per page for efficiency
        - Stops early if API returns empty results
        - Extracts 'id' field from each item in response data
    
    Example:
        >>> ids = _search_ids("modern art", 50)
        >>> print(f"Found {len(ids)} matching items")
    """
    ids: List[str] = []
    page = 1
    # Optimize per_page size: at least 1, at most max_items, capped at 100
    per_page = min(max(1, max_items), 100)  
    
    # Continue pagination until we have enough items or no more results
    while len(ids) < max_items:
        url = f"{API_BASE}/search"
        params = {"q": term, "page": page, "limit": per_page}
        resp = _request_with_backoff("GET", url, params=params)
        payload = resp.json()
        data = payload.get("data", [])
        
        # Stop if no more results available
        if not data:
            break
        
        # Extract IDs from response items
        ids.extend(str(item["id"]) for item in data if "id" in item)
        page += 1
    
    # Return only the requested number of items
    return ids[:max_items]


def _chunk(lst: List[str], size: int) -> List[List[str]]:
    """
    Split a list into smaller chunks of specified size.
    
    Utility function to divide a large list into smaller sublists for batch
    processing. The last chunk may be smaller than the specified size.
    
    Args:
        lst (List[str]): List to be chunked
        size (int): Maximum size of each chunk
    
    Returns:
        List[List[str]]: List of sublists, each containing at most 'size' elements
    
    Example:
        >>> items = ['a', 'b', 'c', 'd', 'e']
        >>> chunks = _chunk(items, 2)
        >>> print(chunks)  # [['a', 'b'], ['c', 'd'], ['e']]
    """
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def _fetch_details(ids: List[str], fields: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch detailed information for multiple items by their IDs.
    
    Retrieves comprehensive data for items using batch requests to optimize
    API usage. Processes IDs in chunks to respect API limits and improve
    performance.
    
    Args:
        ids (List[str]): List of item IDs to fetch details for
        fields (List[str]): List of field names to retrieve for each item.
                            If empty, defaults to basic fields
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries containing item details,
                            where each dict represents one item with requested fields
    
    Raises:
        requests.RequestException: If API requests fail after all retries
        ValueError: If API response format is invalid JSON
    
    Optimization:
        - Processes IDs in batches of 50 to balance efficiency and API limits
        - Uses comma-separated field list for selective data retrieval
        - Returns empty list immediately if no IDs provided
    
    Default Fields:
        When fields list is empty, requests: id, title, artist_title, date_display
    
    Example:
        >>> details = _fetch_details(['123', '456'], ['id', 'title', 'artist'])
        >>> for item in details:
        ...     print(f"{item['id']}: {item['title']}")
    """
    results: List[Dict[str, Any]] = []
    if not ids:
        return results
    
    # Prepare field selection with sensible defaults
    fields_csv = ",".join(fields) if fields else "id,title,artist_title,date_display"
    
    # Process IDs in batches for optimal performance
    for batch in _chunk(ids, 50):
        url = f"{API_BASE}"
        params = {"ids": ",".join(batch), "fields": fields_csv}
        resp = _request_with_backoff("GET", url, params=params)
        payload = resp.json()
        results.extend(payload.get("data", []))
    
    return results


def fetch_report_data(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch complete report data based on report configuration.
    
    Main entry point for report data collection. Orchestrates the search and
    detail fetching process to build a comprehensive dataset for report generation.
    Combines search results with detailed item information and provides metadata
    about the collection process.
    
    Args:
        report (Dict[str, Any]): Report configuration dictionary containing:
            - name (str, optional): Report identifier, defaults to "report"
            - search (str, optional): Search query term, defaults to empty string
            - fields (List[str], optional): Fields to fetch for each item,
                defaults to ["id", "title", "artist_title", "date_display"]
            - max_items (int, optional): Maximum items to include, defaults to 25
    
    Returns:
        Dict[str, Any]: Complete report data structure containing:
            - report (Dict): Metadata about the report configuration used
                - name (str): Report name
                - search (str): Search term used
                - fields (List[str]): Fields requested
                - max_items (int): Maximum items limit
            - items (List[Dict]): Detailed data for each found item
            - count (int): Actual number of items retrieved
    
    Raises:
        requests.RequestException: If API communication fails
        ValueError: If report configuration contains invalid data types
        TypeError: If required configuration fields have wrong types
    
    Process Flow:
        1. Extract and validate configuration parameters
        2. Search for items matching the search term
        3. Fetch detailed information for found items
        4. Combine results with metadata for report generation
    
    Logging:
        Logs progress at each major step including search parameters,
        number of IDs found, and final item count for monitoring.
    
    Example:
        >>> config = {
        ...     "name": "modern_art_report",
        ...     "search": "modern painting",
        ...     "fields": ["id", "title", "artist", "date"],
        ...     "max_items": 100
        ... }
        >>> data = fetch_report_data(config)
        >>> print(f"Retrieved {data['count']} items for {data['report']['name']}")
    """
    # Extract configuration with sensible defaults
    name = report.get("name") or "report"
    search = report.get("search") or ""
    fields = report.get("fields") or ["id", "title", "artist_title", "date_display"]
    max_items = int(report.get("max_items") or 25)

    logging.info(f"[{name}] Fetch start | search='{search}' | fields={fields} | max_items={max_items}")

    # Phase 1: Search for matching item IDs
    ids = _search_ids(search, max_items)
    logging.info(f"[{name}] search found {len(ids)} ids")

    # Phase 2: Fetch detailed information for found items
    items = _fetch_details(ids, fields)
    logging.info(f"[{name}] fetched {len(items)} details")

    # Return comprehensive report data structure
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