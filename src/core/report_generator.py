import os
import json
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_report(data):
    os.makedirs("artifacts/json", exist_ok=True)
    os.makedirs("artifacts/pdf", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = f"artifacts/json/report_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    logging.info(f"JSON saved at {json_path}")

    pdf_path = f"artifacts/pdf/report_{timestamp}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Artworks Report")
    y = 700
    for item in data:
        c.drawString(100, y, str(item))
        y -= 20
    c.save()
    logging.info(f"PDF saved at {pdf_path}")

    return pdf_path, json_path