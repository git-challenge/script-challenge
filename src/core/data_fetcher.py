import logging


def fetch_artworks(search, fields, limit):
    # TODO: Implement actual data fetching logic
    logging.info(f"Fetching {limit} artworks for search='{search}' with fields={fields}")
    data = []
    
    for i in range(limit):
        entry = {field: f"{field}_{i}" for field in fields}
        data.append(entry)
    
    return data