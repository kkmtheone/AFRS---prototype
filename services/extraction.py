# services/extraction.py

import fitz  # PyMuPDF
import re

def extract_numbers_from_pdf(file_bytes: bytes) -> dict:
    """
    Extract key financial numbers from a PDF file.
    Uses simple regex patterns — adapt them to your statements' format.
    """

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""

    for page in doc:
        text += page.get_text()

    # Clean text: remove currency symbols, weird spaces, etc.
    text = text.replace(",", "").replace("Ksh", "").replace("KES", "").replace("Shs", "")

    def find_value(keywords):
        for keyword in keywords:
            pattern = rf"{keyword}[^0-9\-]*([\d\.]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).strip())
                except ValueError:
                    continue
        return 0.0

    data = {
        "share_capital": find_value(["Share Capital", "Paid Up Capital"]),
        "liquid_capital": find_value(["Liquid Capital", "Working Capital"]),
        "net_assets": find_value(["Net Assets", "Total Net Assets"]),
        "total_liabilities": find_value(["Total Liabilities", "Liabilities Total"]),
    }

    return data
