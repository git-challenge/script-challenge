"""
Report Generation and Email Distribution System

This module provides a command-line interface for generating reports from configured queries,
rendering them as PDFs, and optionally distributing them via email. It supports batch processing
of multiple reports with error handling, logging, and runtime limits.

Dependencies:
    - click: Command-line interface framework
    - dotenv: Environment variable management
    - Custom modules: src.utils, src.core

Author: Juan Sebastián Dosman
Version: 1.0
Date: 15th August 2025
"""

import os
import sys
import time   
import click
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List
from src.utils import setup_logging, load_queries, resolve_path, write_json, utc_now_str, sanitize_filename, get_env_int
from src.core import fetch_report_data, render_pdf, send_email


# Load environment variables from .env file
load_dotenv() 


@click.command(name="run")
@click.option("--config", default="config/queries.yml", show_default=True, help="Path to YAML configuration file.")
@click.option("--out", default="out", show_default=True, help="Output directory for PDFs/JSON/logs.")
@click.option("--dry-run", is_flag=True, help="Generate artifacts but skip email sending.")
@click.option("--max-runtime", default=None, type=int, help="Maximum runtime in seconds (overrides MAX_RUNTIME env var).")
def main(config: str, out: str, dry_run: bool, max_runtime: int | None) -> None:
    """
    Main entry point for the report generation system.
    
    This function orchestrates the entire report generation workflow including:
    - Loading configuration from YAML file
    - Processing multiple reports in batch
    - Generating JSON data files and PDF reports
    - Optionally sending reports via email
    - Creating execution summaries with success/failure metrics
    - Enforcing runtime limits to prevent long-running jobs
    
    Args:
        config (str): Path to the YAML configuration file containing report definitions.
                    Defaults to "config/queries.yml"
        out (str): Output directory path where generated files will be stored.
                    Defaults to "out"
        dry_run (bool): When True, generates all artifacts but skips email sending.
                    Useful for testing and validation
        max_runtime (int | None): Maximum execution time in seconds. If provided,
                    overrides the MAX_RUNTIME environment variable.
                    When None, uses environment variable or no limit
    
    Returns:
        None
    
    Raises:
        click.ClickException: When configuration file is invalid or contains no reports
        SystemExit: When one or more reports fail to process (exit code 1)
    
    Side Effects:
        - Creates output directory if it doesn't exist
        - Sets up logging to file in output directory
        - Writes JSON data files for each report
        - Generates PDF files for each report
        - Sends emails (unless dry_run is True)
        - Creates summary.json with execution results
        - Logs all operations and errors
    
    Example:
        >>> # Generate reports with default settings
        >>> main("config/reports.yml", "output", False, None)
        
        >>> # Dry run with custom timeout
        >>> main("config/test.yml", "test_out", True, 300)
    """
    # Initialize output directory and logging
    os.makedirs(resolve_path(out), exist_ok=True)
    setup_logging(resolve_path(out))
    
    # Initialize tracking variables
    summary: List[Dict[str, Any]] = []
    failures = 0

    # Determine maximum runtime limit
    max_runtime_env = get_env_int("MAX_RUNTIME", 0)
    max_runtime = max_runtime or max_runtime_env  
    start_ts = time.time()  

    # Load and validate configuration
    try:
        cfg = load_queries(config)
        reports = cfg.get("reports", [])
        
        if not reports:
            raise click.ClickException("No reports defined in configuration.")
    except Exception as e:
        logging.exception("Failed to load configuration")
        click.get_current_context().exit(1)

    # Process each report in the configuration
    for rpt in reports:
        name = rpt.get("name") or "report"
        safe_name = sanitize_filename(name)
        
        try:
            # Fetch report data from configured source
            data = fetch_report_data(rpt)
            
            # Save raw data as JSON
            json_path = resolve_path(out, f"{safe_name}.json")
            write_json(data, json_path)
            
            # Generate PDF report
            pdf_path = resolve_path(out, f"{safe_name}.pdf")
            render_pdf(rpt, data, pdf_path, save_html=True)

            # Send email unless in dry-run mode
            if not dry_run:
                send_email(rpt, pdf_path, json_path)

            # Record successful processing
            summary.append({
                "name": name,
                "count": data.get("count", 0),
                "json": os.path.relpath(json_path, resolve_path(out)),
                "pdf": os.path.relpath(pdf_path, resolve_path(out)),
                "status": "ok",
            })
            logging.info(f"[{name}] done | items={data.get('count', 0)} | dry_run={dry_run}")

        except Exception as e:
            # Record failed processing
            failures += 1
            logging.exception(f"[{name}] failed")
            summary.append({
                "name": name,
                "status": "failed",
                "error": str(e),
            })

        # Check runtime limit and abort if exceeded
        if max_runtime and (time.time() - start_ts) > max_runtime:  
            logging.error(f"Max runtime exceeded ({max_runtime}s). Aborting.")
            break

    # Generate execution summary
    job_summary = {
        "generated_at": utc_now_str(),
        "dry_run": dry_run,
        "reports_total": len(reports),
        "reports_ok": sum(1 for s in summary if s.get("status") == "ok"),
        "reports_failed": sum(1 for s in summary if s.get("status") == "failed"),
        "reports": summary,
    }
    write_json(job_summary, resolve_path(out, "summary.json"))

    # Display final results
    click.echo(f"Summary: ok={job_summary['reports_ok']} failed={job_summary['reports_failed']} dry_run={dry_run}")
    
    # Exit with error code if any reports failed
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()