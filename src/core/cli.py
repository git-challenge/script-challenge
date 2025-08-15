import os
import sys
import time   
import click
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List
from src.utils import setup_logging, load_queries, resolve_path, write_json, utc_now_str, sanitize_filename, get_env_int
from src.core import fetch_report_data, render_pdf, send_email


load_dotenv() 

@click.command(name="run")
@click.option("--config", default="config/queries.yml", show_default=True, help="Ruta al YAML de configuración.")
@click.option("--out", default="out", show_default=True, help="Directorio de salida para PDFs/JSON/logs.")
@click.option("--dry-run", is_flag=True, help="Genera artefactos pero no envía correos.")
@click.option("--max-runtime", default=None, type=int, help="Tiempo máximo (seg) para el job (override de env MAX_RUNTIME).")
def main(config: str, out: str, dry_run: bool, max_runtime: int | None):
    os.makedirs(resolve_path(out), exist_ok=True)
    setup_logging(resolve_path(out))
    summary: List[Dict[str, Any]] = []
    failures = 0

    max_runtime_env = get_env_int("MAX_RUNTIME", 0)
    max_runtime = max_runtime or max_runtime_env  
    start_ts = time.time()  

    try:
        cfg = load_queries(config)
        reports = cfg.get("reports", [])
        
        if not reports:
            raise click.ClickException("No reports defined in configuration.")
    except Exception as e:
        logging.exception("Failed to load configuration")
        click.get_current_context().exit(1)

    for rpt in reports:
        name = rpt.get("name") or "report"
        safe_name = sanitize_filename(name)
        
        try:
            data = fetch_report_data(rpt)
            
            json_path = resolve_path(out, f"{safe_name}.json")
            write_json(data, json_path)
            
            pdf_path = resolve_path(out, f"{safe_name}.pdf")
            render_pdf(rpt, data, pdf_path, save_html=True)

            if not dry_run:
                send_email(rpt, pdf_path, json_path)

            summary.append({
                "name": name,
                "count": data.get("count", 0),
                "json": os.path.relpath(json_path, resolve_path(out)),
                "pdf": os.path.relpath(pdf_path, resolve_path(out)),
                "status": "ok",
            })
            logging.info(f"[{name}] done | items={data.get('count', 0)} | dry_run={dry_run}")

        except Exception as e:
            failures += 1
            logging.exception(f"[{name}] failed")
            summary.append({
                "name": name,
                "status": "failed",
                "error": str(e),
            })

        if max_runtime and (time.time() - start_ts) > max_runtime:  
            logging.error(f"Max runtime exceeded ({max_runtime}s). Aborting.")
            break

    job_summary = {
        "generated_at": utc_now_str(),
        "dry_run": dry_run,
        "reports_total": len(reports),
        "reports_ok": sum(1 for s in summary if s.get("status") == "ok"),
        "reports_failed": sum(1 for s in summary if s.get("status") == "failed"),
        "reports": summary,
    }
    write_json(job_summary, resolve_path(out, "summary.json"))

    click.echo(f"Summary: ok={job_summary['reports_ok']} failed={job_summary['reports_failed']} dry_run={dry_run}")
    if failures:
        sys.exit(1)

if __name__ == "__main__":
    main()  