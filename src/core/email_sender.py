"""
Email Sending Module for Report Distribution (HTML Enhanced)

This module sends generated reports as email attachments with a polished,
responsive HTML email template, while also including a plain-text fallback.

Key Features:
    - HTML email body styled with CSS (external template)
    - Jinja2 templating for dynamic content injection
    - Secure SMTP connection with STARTTLS encryption
    - Multiple recipient support
    - PDF and JSON file attachment handling
    - Base64 encoding for binary attachments
    - Comprehensive error handling and logging
    - Environment variable configuration for security

Required Environment Variables:
    SMTP_HOST: SMTP server hostname (e.g., smtp.gmail.com)
    SMTP_PORT: SMTP server port (e.g., 587 for TLS)
    SMTP_USER: SMTP authentication username/email
    SMTP_PASS: SMTP authentication password/token

Security Notes:
    - Uses STARTTLS for encrypted connections
    - Credentials loaded from environment variables only
    - No credential storage in code or logs
    - Supports modern SMTP authentication methods

Dependencies:
    - smtplib: Built-in SMTP client
    - email.mime.*: Email message construction
    - dotenv: Environment variable management
    - jinja2 for HTML template rendering

Author: Juan Sebastián Dosman
Version: 1.0
Date: 15th August 2025
"""

import os
import logging
import smtplib
from typing import Dict, Any, List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv() 


def _env_required(key: str) -> str:
    """
    Retrieve a required environment variable with validation.
    
    This function ensures that critical configuration values are present
    in the environment. It provides clear error messages when required
    variables are missing, helping with deployment and configuration issues.
    
    Args:
        key (str): The name of the environment variable to retrieve
    
    Returns:
        str: The value of the environment variable
    
    Raises:
        RuntimeError: If the environment variable is not set or is empty
    
    Security Note:
        This function is used for sensitive configuration like SMTP credentials.
        It ensures the application fails fast if security-critical variables
        are missing rather than using unsafe defaults.
    
    Example:
        >>> smtp_host = _env_required("SMTP_HOST")
        >>> # Raises RuntimeError if SMTP_HOST is not set
    """
    val = os.getenv(key)
    
    if not val:
        raise RuntimeError(f"Missing required env var: {key}")
    
    return val


def _attach_file(msg: MIMEMultipart, file_path: str) -> None:
    """
    Attach a file to an email message as a binary attachment.
    
    This function handles the process of reading a file, encoding it as base64,
    and attaching it to an email message with proper MIME headers. It supports
    any file type by using the generic 'application/octet-stream' MIME type.
    
    Args:
        msg (MIMEMultipart): The email message object to attach the file to
        file_path (str): Full path to the file to be attached
    
    Returns:
        None: Modifies the msg object in place
    
    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If the file cannot be read due to permissions
        OSError: If there are other file system errors during reading
    
    MIME Handling:
        - Uses 'application/octet-stream' for universal binary file support
        - Encodes file content as base64 for email transmission
        - Sets Content-Disposition header for proper client handling
        - Preserves original filename in the attachment
    
    Example:
        >>> msg = MIMEMultipart()
        >>> _attach_file(msg, "/path/to/report.pdf")
        >>> # File is now attached to the email message
    """
    with open(file_path, "rb") as f:
        # Create MIME part for binary attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        
        # Encode file content as base64 for email transmission
        encoders.encode_base64(part)
        
        # Set filename for download/display in email clients
        filename = os.path.basename(file_path)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        
        # Attach the part to the main message
        msg.attach(part)



def _render_email_html(report_name: str, has_json: bool) -> str:
    """
    Render an HTML email body from a predefined template with dynamic report details.
    
    This function loads the `email-template.html` file from the project's `templates` 
    directory and injects dynamic values into placeholders to generate the final HTML 
    content for an email notification. It is primarily used to notify users about the 
    generation of a report, optionally including a JSON reference if available.
    
    Args:
        report_name (str): The name of the generated report (used in both subject and body)
        has_json (bool): Flag indicating if a JSON version of the report is available.
                        If True, the text "and JSON" will be appended to the report type.
    
    Returns:
        str: The fully rendered HTML string ready to be sent as an email body.
    
    Raises:
        FileNotFoundError: If the `email-template.html` file cannot be found.
        TemplateError: If Jinja2 encounters an error while parsing or rendering the template.
    
    Template Variables:
        - subject: The subject line for the email (e.g., "Report: Artworks-2025-08-14")
        - report_name: The base name of the report
        - has_json: The string `" and JSON"` if a JSON file is included, otherwise `""`
    
    Example:
        >>> html = _render_email_html("Artworks-2025-08-14", True)
        >>> print(html)  # Displays the complete HTML email with placeholders replaced
    
    Notes:
        - Templates are stored in `src/templates/email-template.html` relative to this file.
        - The HTML template must define placeholders for the injected variables.
        - Uses Jinja2's `FileSystemLoader` to locate and render the template.
    """
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("email-template.html")
    
    return template.render(
        subject=f"Report: {report_name}",
        report_name=report_name,
        has_json=" and JSON" if has_json else ""
    )


def send_email(report_cfg: Dict[str, Any], pdf_path: str, json_path: Optional[str] = None) -> None:
    """
    Send report files via email to configured recipients.
    
    This function orchestrates the complete email sending process including
    recipient validation, SMTP configuration, message construction, file
    attachment, and secure transmission. It handles both PDF and optional
    JSON attachments for comprehensive report distribution.
    
    Args:
        report_cfg (Dict[str, Any]): Report configuration dictionary containing:
            - recipients (List[str], optional): List of recipient email addresses
            - name (str, optional): Report name used in subject and logging
        pdf_path (str): Path to the PDF report file to attach (required)
        json_path (Optional[str]): Path to JSON data file to attach (optional).
                                Only attached if path exists and file is present
    
    Returns:
        None
    
    Raises:
        RuntimeError: If required environment variables are missing
        FileNotFoundError: If the PDF file doesn't exist
        smtplib.SMTPAuthenticationError: If SMTP authentication fails
        smtplib.SMTPConnectError: If connection to SMTP server fails
        smtplib.SMTPRecipientsRefused: If recipient addresses are invalid
        smtplib.SMTPException: For other SMTP-related errors
        OSError: For file system errors when reading attachments
    
    Email Configuration:
        - Uses SMTP with STARTTLS for secure transmission
        - Authenticates using SMTP_USER and SMTP_PASS environment variables
        - Supports multiple recipients (comma-separated in To: header)
        - Sets subject line with report name
        - Includes basic plain text body
    
    Attachment Behavior:
        - PDF file is always attached (required)
        - JSON file is conditionally attached if path provided and file exists
        - Files are base64 encoded for binary transmission
        - Original filenames are preserved in attachments
    
    Environment Variables Required:
        - SMTP_HOST: SMTP server hostname
        - SMTP_PORT: SMTP server port number
        - SMTP_USER: Authentication username (used as From address)
        - SMTP_PASS: Authentication password or app token
    
    Logging:
        Logs email sending attempts with recipient count for monitoring.
        Does not log sensitive information like credentials or recipient addresses.
    
    Example:
        >>> config = {
        ...     "name": "Sales Report Q4",
        ...     "recipients": ["manager@company.com", "sales@company.com"]
        ... }
        >>> send_email(config, "/reports/sales_q4.pdf", "/reports/sales_q4.json")
        
        >>> # Skip email if no recipients configured
        >>> config_no_recipients = {"name": "Test Report"}
        >>> send_email(config_no_recipients, "/reports/test.pdf")
        >>> # Logs warning and returns without sending
    """
    # Extract configuration with validation
    recipients: List[str] = list(report_cfg.get("recipients") or [])
    name = report_cfg.get("name") or "report"

    # Skip sending if no recipients configured
    if not recipients:
        logging.warning(f"[{name}] No recipients defined; skipping email send.")
        return

    # Load SMTP configuration from environment variables
    host = _env_required("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT"))
    user = _env_required("SMTP_USER")
    password = _env_required("SMTP_PASS")

    # Determine if JSON file exists
    has_json = json_path and os.path.exists(json_path)

    # Construct email message
    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"Report: {name}"

    # Create alternative part for plain text and HTML
    alt_part = MIMEMultipart("alternative")
    plain_body = f"Attached report '{name}' in PDF{' and JSON' if has_json else ''} format."
    html_body = _render_email_html(name, has_json)
    alt_part.attach(MIMEText(plain_body, "plain"))
    alt_part.attach(MIMEText(html_body, "html"))
    msg.attach(alt_part)

    # Attachments
    _attach_file(msg, pdf_path)
    if has_json:
        _attach_file(msg, json_path)

    # Send email via SMTP with secure connection
    logging.info(f"[{name}] sending email to {len(recipients)} recipient(s)")
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)