import sys
from src.config import setup_logging
from src.core import build_parser
from src.main import run_report


def main():
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    try:
        run_report(args)
    except Exception as e:
        import logging
        logging.exception("Error executing report")
        sys.exit(1)

if __name__ == "__main__":
    main()