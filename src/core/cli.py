import argparse


def build_parser():
    parser = argparse.ArgumentParser(description="Artworks Report Generator")
    parser.add_argument("--search", type=str, required=True, help="Search term for artworks")
    parser.add_argument("--fields", type=str, required=True, help="Comma-separated fields to include")
    parser.add_argument("--artworks", type=int, default=5, help="Number of artworks to fetch")
    parser.add_argument("-m", "--email", type=str, help="Email to send report to")
    parser.add_argument("--dry-run", action="store_true", help="Generate preview only (no email send)")
    
    return parser