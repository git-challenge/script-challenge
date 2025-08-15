"""
Entry point for the Artworks Report Generator script.

This module serves as the executable entry point for the application.
When run directly from the command line, it will invoke the CLI interface
defined in `src.core.cli.main()`.

The CLI handles:
    - Parsing command-line arguments.
    - Loading the YAML configuration file.
    - Fetching data from the Art Institute of Chicago API.
    - Generating JSON and PDF reports.

Usage:
    python -m artworks-report.py --config config/queries.yml --out out

Author: Juan Sebastián Dosman
Version: 1.0
Date: 15th August 2025
"""

from src.core.cli import main


if __name__ == "__main__":
    # Call the main CLI entry function when executed directly
    main()