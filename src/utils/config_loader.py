import os
import yaml


def load_queries(path):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    full_path = os.path.join(base_dir, path)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Configuration file not found: {full_path}")

    with open(full_path, "r") as f:
        return yaml.safe_load(f)