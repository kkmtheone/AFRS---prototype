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

    share_capital = find_value(["Share Capital", "Share capital", "share capital", "Paid Up Capital", "Paid Up capital", "Paid up capital", "paid up capital"])
    liquid_capital = find_value(["Liquid Capital", "Liquid capital", "liquid capital", "Working Capital", "Working capital", "working capital"])
    net_assets = find_value(["Net Assets", "Net assets", "net assets", "Total Net Assets", "Total Net assets", "Total net assets", "total net assets"])
    current_assets = find_value(["Current assets", "Current Assets", "current assets"])
    inventories = find_value(["Inventories", "inventories", "Inventory", "inventory"])
    non_current_assets = find_value(["Non-current Assets", "Non-Current Assets", "Non-current assets", "non-current assets", "Non Current Assets", "Non Current assets", "Non current assets", "non current assets"])
    non_current_liabilities = find_value(["Non-Current Liabilities", "Non-Current liabilities", "Non-current liabilities", "non-current liabilities", "Non Current Liabilities", "Non Current liabilities", "Non current liabilities", "non current liabilities"])
    current_liabilities = find_value(["Current Liabilities", "Current liabilities", "current liabilities"])
    other_liquid_assets = find_value(["Other Financial Assets", "Other Financial assets", "Other financial assets", "other financial assets", "Other Liquid Assets", "Other Liquid assets", "Other liquid assets", "other liquid assets"])
    cash = find_value(["cash", "Cash"])
    cash_equivalents = find_value(["Cash Equivalents", "Cash Equivalent", "Cash equivalents", "cash equivalents", "Cash equivalent", "cash equivalent"])
    bank_balances = find_value(["Bank Balance", "Bank balance", "bank balance", "Bank Balances", "Bank balances", "bank balances", "Bank and cash balances", "Bank and Cash Balances", "Bank and Cash balances", "Bank and cash balances", "bank and cash balances", "Bank and Cash Balance", "Bank and Cash balance", "Bank and cash balance", "bank and cash balance", "Bank Account Balances", "Bank Account balances", "Bank account balances", "bank account balances", "Bank Account Balance", "Bank Account balance", "Bank account balance", "bank account balance"])
    due_from_related_companies = find_value(["Due from related companies", "Due from related companies-current"])
    prepaid_expenses = find_value(["Prepaid Expenses", "Prepaid expenses", "prepaid expenses", "Prepaid Expense", "Prepaid expense", "prepaid expense"])
    marketable_securities = find_value(["Marketable Securities", "Marketable securities", "marketable securities", "Marketable Assets", "Marketable assets", "marketables assets"])
    accounts_receivables = find_value(["receivables", "Receivables","receivable", "receivable", "Account Receivables", "Account receivables", "account receivables", "Account Receivable", "Account receivable", "account receivable", "Accounts Receivables", "Accounts receivables", "accounts receivables", "Trade and other receivables"])

    total_assets = find_value(["Total Assets", "Total assets", "total assets", "Assets Total","Assets total", "assets total", "Assets", "assets"])
    total_liabilities = find_value(["Total Liabilities", "Total liabilities", "total liabilities", "Liabilities Total", "Liabilities total", "liabilities total", "Liabilities", "liabilities"])

    if net_assets == 0.0 and total_assets and total_liabilities:
        net_assets = total_assets - total_liabilities

    if current_assets = 0.0 and (cash or cash_equivalents or inventories or accounts_receivables or marketable_securities or prepaid_expenses or other_liquid_assets or bank_balances or due_from_related_companies):
        current_assets = cash + cash_equivalents + inventories + accounts_receivables + marketable_securities + prepaid_expenses + other_liquid_assets + bank_balances + due_from_related_companies

    if liquid_capital = 0.0 and current_assets and inventories:
        liquid_capital = current_assets - inventories
    
    if total_liabilities = 0.0 and non_current_liabilities and current_liabilities:
        total_liabilities = non_current_liabilities + current_liabilities
    
    if total_assets = 0.0 and non_current_assets and current_assets:
        total_assets = non_current_assets + current_assets

    return {
        "share_capital": share_capital,
        "liquid_capital": liquid_capital,
        "net_assets": net_assets,
        "total_liabilities": total_liabilities,
        "total_assets": total_assets,  
    }
