"""
PDF Report Rendering Module

This module provides HTML-to-PDF conversion functionality for generating
professional report documents. It uses Jinja2 templating for flexible
HTML generation and WeasyPrint for high-quality PDF rendering with
CSS styling support.

Key Features:
    - Template-based HTML generation using Jinja2
    - High-quality PDF rendering with CSS support
    - Automatic security through template autoescape
    - Optional HTML file output for debugging
    - Flexible context data binding
    - UTF-8 encoding support for international content
    - Project-relative template loading

Template Requirements:
    - Templates must be stored in project_root()/templates/ directory
    - Primary template file should be named 'report-template.html'
    - Templates have access to generated_at, report, items, and count variables
    - CSS styling is supported through WeasyPrint's CSS engine

Dependencies:
    - jinja2: Template engine for HTML generation
    - weasyprint: HTML to PDF conversion library
    - src.utils: Project utilities for path resolution and timestamps

Output Formats:
    - PDF: Primary output format for distribution
    - HTML: Optional debug output with same filename + .html extension

Author: Juan Sebastián Dosman
Version: 1.0
Date: 15th August 2025
"""

import logging
import os
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from src.utils import project_root, resolve_path, utc_now_str


def _jinja_env() -> Environment:
    """
    Create and configure a Jinja2 template environment for report rendering.
    
    Sets up a secure Jinja2 environment with automatic HTML/XML escaping
    to prevent XSS vulnerabilities and configures template loading from
    the project's templates directory.
    
    Returns:
        Environment: Configured Jinja2 environment ready for template rendering
    
    Raises:
        jinja2.TemplateNotFound: If templates directory doesn't exist
        OSError: If there are file system access issues
    
    Security Features:
        - Automatic HTML and XML escaping enabled for security
        - Templates loaded from controlled directory only
        - No unsafe template loading from user input
    
    Configuration:
        - Template directory: project_root()/templates/
        - Autoescape: Enabled for HTML and XML content
        - Loader: FileSystemLoader for secure file-based templates
    
    Example:
        >>> env = _jinja_env()
        >>> template = env.get_template("report-template.html")
        >>> html = template.render(data=my_data)
    """
    templates_dir = os.path.join(project_root(), "templates")
    
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"])
    )


def render_pdf(report_cfg: Dict[str, Any], data: Dict[str, Any], pdf_path: str, save_html: bool = True) -> None:
    """
    Render report data to PDF using HTML templates.
    
    This function orchestrates the complete PDF generation process from template
    rendering through HTML generation to final PDF output. It provides a complete
    workflow for creating professional reports with consistent formatting and
    optional debugging output.
    
    Args:
        report_cfg (Dict[str, Any]): Report configuration dictionary containing:
            - name (str, optional): Report name for logging and context
            - Any other configuration values accessible in templates
        data (Dict[str, Any]): Report data dictionary containing:
            - items (List[Dict], optional): List of data items to display
            - count (int, optional): Total count of items
            - Any other data values accessible in templates
        pdf_path (str): Target file path for the generated PDF output
        save_html (bool, optional): Whether to save intermediate HTML file
                                for debugging. Defaults to True
    
    Returns:
        None
    
    Raises:
        jinja2.TemplateNotFound: If 'report-template.html' template doesn't exist
        jinja2.TemplateError: If template rendering fails due to syntax errors
        weasyprint.HTML.Error: If PDF generation fails
        OSError: If output directories cannot be created or files cannot be written
        UnicodeError: If there are encoding issues with template or data
    
    Template Context:
        The following variables are automatically available in templates:
        - generated_at (str): UTC timestamp of generation
        - report (Dict): Complete report configuration
        - items (List): Data items for display (empty list if not provided)
        - count (int): Number of items (0 if not provided)
    
    File Operations:
        - Creates output directory if it doesn't exist
        - Generates PDF at specified path
        - Optionally saves HTML debug file with same base name
        - Uses UTF-8 encoding for all text operations
    
    PDF Generation:
        - Uses WeasyPrint for high-quality PDF rendering
        - Supports CSS styling including print-specific styles
        - Handles fonts, images, and complex layouts
        - Uses project root as base URL for relative resource resolution
    
    HTML Debug Output:
        When save_html=True:
        - Creates HTML file with same path as PDF but .html extension
        - Useful for debugging template rendering and CSS issues
        - Contains exact HTML that was converted to PDF
    
    Logging:
        Logs PDF generation attempts with report name and output path
        for monitoring and debugging purposes.
    
    Example:
        >>> config = {"name": "Sales Report", "title": "Q4 Sales"}
        >>> data = {
        ...     "items": [{"product": "Widget", "sales": 100}],
        ...     "count": 1
        ... }
        >>> render_pdf(config, data, "/reports/sales_q4.pdf")
        >>> # Creates sales_q4.pdf and sales_q4.html
        
        >>> # Skip HTML debug output
        >>> render_pdf(config, data, "/reports/final.pdf", save_html=False)
        >>> # Creates only final.pdf
    
    Template Example:
        A basic report-template.html template might look like:
        ```html
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ report.name }}</title>
            <style>
                body { font-family: Arial, sans-serif; }
                .header { color: #333; }
            </style>
        </head>
        <body>
            <h1 class="header">{{ report.name }}</h1>
            <p>Generated: {{ generated_at }}</p>
            <p>Total items: {{ count }}</p>
            {% for item in items %}
                <div>{{ item.name }}: {{ item.value }}</div>
            {% endfor %}
        </body>
        </html>
        ```
    """
    # Initialize template environment and load template
    env = _jinja_env()
    template = env.get_template("report-template.html")

    # Prepare template context with report data and metadata
    ctx = {
        "generated_at": utc_now_str(),
        "report": report_cfg,
        "items": data.get("items", []),
        "count": data.get("count", 0),
    }
    
    # Render template to HTML string
    html_str = template.render(**ctx)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    # Optionally save HTML debug output
    if save_html:
        html_path = os.path.splitext(pdf_path)[0] + ".html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_str)

    # Generate PDF from HTML
    logging.info(f"[{report_cfg.get('name')}] rendering PDF -> {pdf_path}")
    HTML(string=html_str, base_url=project_root()).write_pdf(pdf_path)