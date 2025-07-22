import fitz
import re

def extract_numbers_from_pdf(file_bytes: bytes) -> dict:
    """
    Extract key financial numbers from PDF text.
    Detects unit scale (thousands, millions) and does basic math for derived fields.
    """

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""

    for page in doc:
        text += page.get_text()

    text = text.replace(",", "").replace("Ksh", "").replace("KES", "").replace("Shs", "")

    scale = 1
    if re.search(r'in thousands', text, re.IGNORECASE):
        scale = 1_000
    elif re.search(r'in millions', text, re.IGNORECASE):
        scale = 1_000_000

    def find_value(keywords):
        for keyword in keywords:
            pattern = rf"{keyword}[^0-9\-]*([\d\.]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).strip()) * scale
                except ValueError:
                    continue
        return 0.0

    share_capital = find_value(["Share Capital", "Paid Up Capital"])
    liquid_capital = find_value(["Liquid Capital", "Working Capital"])
    net_assets = find_value(["Net Assets", "Total Net Assets"])

    total_assets = find_value(["Total Assets", "Assets Total"])
    total_liabilities = find_value(["Total Liabilities", "Liabilities Total"])

    if net_assets == 0.0 and total_assets and total_liabilities:
        net_assets = total_assets - total_liabilities

    return {
        "share_capital": share_capital,
        "liquid_capital": liquid_capital,
        "net_assets": net_assets,
        "total_liabilities": total_liabilities,
        "total_assets": total_assets,  
    }
