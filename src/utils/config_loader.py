import yaml


def load_queries(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)