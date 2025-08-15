import os
import sys
import json
import time
import logging
import yaml
from datetime import datetime, timezone
from typing import Any, Dict
from pathlib import Path
from dotenv import load_dotenv


load_dotenv() 

def project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def resolve_path(*parts: str) -> str:
    root_dir = Path(__file__).resolve().parents[2]
    
    return root_dir.joinpath(*parts)

def load_queries(config_path: str = "config/queries.yml") -> Dict[str, Any]:
    full_path = resolve_path(config_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Configuration file not found: {full_path}")
    
    with open(full_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    if "reports" not in data or not isinstance(data["reports"], list):
        raise ValueError("Invalid queries.yml: root key 'reports' must be a list")
    
    return data

def setup_logging(out_dir: str) -> None:
    logs_dir = os.path.join(out_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_path = os.path.join(logs_dir, "run.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8")
        ]
    )

def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def write_json(obj: Any, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def sanitize_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".")).strip()

def get_env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

def bounded_sleep(seconds: float) -> None:
    try:
        time.sleep(max(0.0, seconds))
    except Exception:
        pass