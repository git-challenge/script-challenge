import os
import json
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_report(data):
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Guardar JSON
    json_path = f"data/report_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
    logging.info(f"JSON saved at {json_path}")

    # Generar PDF básico
    pdf_path = f"reports/report_{timestamp}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Artworks Report")
    y = 700
    for item in data:
        c.drawString(100, y, str(item))
        y -= 20
    c.save()
    logging.info(f"PDF saved at {pdf_path}")

    return pdf_path, json_path