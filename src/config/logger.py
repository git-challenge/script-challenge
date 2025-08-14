import logging
import os


def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/run.log",
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )