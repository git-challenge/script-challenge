import logging
import os
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from src.utils import project_root, resolve_path, utc_now_str


def _jinja_env() -> Environment:
    templates_dir = os.path.join(project_root(), "templates")
    
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"])
    )

def render_pdf(report_cfg: Dict[str, Any], data: Dict[str, Any], pdf_path: str, save_html: bool = True) -> None:
    env = _jinja_env()
    template = env.get_template("report.html")

    ctx = {
        "generated_at": utc_now_str(),
        "report": report_cfg,
        "items": data.get("items", []),
        "count": data.get("count", 0),
    }
    html_str = template.render(**ctx)

    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    if save_html:
        html_path = os.path.splitext(pdf_path)[0] + ".html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_str)

    logging.info(f"[{report_cfg.get('name')}] rendering PDF -> {pdf_path}")
    HTML(string=html_str, base_url=project_root()).write_pdf(pdf_path)