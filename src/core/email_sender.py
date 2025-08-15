import os
import logging
import smtplib
from typing import Dict, Any, List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv


load_dotenv() 

def _env_required(key: str) -> str:
    val = os.getenv(key)
    
    if not val:
        raise RuntimeError(f"Missing required env var: {key}")
    
    return val

def _attach_file(msg: MIMEMultipart, file_path: str) -> None:
    with open(file_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = os.path.basename(file_path)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

def send_email(report_cfg: Dict[str, Any], pdf_path: str, json_path: Optional[str] = None) -> None:
    recipients: List[str] = list(report_cfg.get("recipients") or [])
    name = report_cfg.get("name") or "report"

    if not recipients:
        logging.warning(f"[{name}] No recipients defined; skipping email send.")
        return

    host = _env_required("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT"))
    user = _env_required("SMTP_USER")
    password = _env_required("SMTP_PASS")

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"Report: {name}"
    msg.attach(MIMEText(f"Attached report '{name}'.", "plain"))

    _attach_file(msg, pdf_path)
    if json_path and os.path.exists(json_path):
        _attach_file(msg, json_path)

    logging.info(f"[{name}] sending email to {len(recipients)} recipient(s)")
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)