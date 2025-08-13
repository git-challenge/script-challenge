import logging
from src.utils import load_queries
from src.core import fetch_artworks, generate_report, send_email


def run_report(args):
    logging.info("Loading configuration...")
    queries = load_queries("config/queries.yml")

    logging.info("Fetching data...")
    data = fetch_artworks(
        search=args.search,
        fields=args.fields.split(","),
        limit=args.artworks
    )

    logging.info("Generating report...")
    pdf_path, json_path = generate_report(data)

    if not args.dry_run and args.email:
        logging.info(f"Sending report to {args.email}")
        send_email(args.email, pdf_path, json_path)

    logging.info("Done.")