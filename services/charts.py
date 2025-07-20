# services/charts.py

import matplotlib.pyplot as plt
import io
import base64

def generate_trend_chart(reports):
    """
    Takes a list of FinancialReport, returns a base64 PNG.
    """
    years = [r.year for r in reports]
    capitals = [r.share_capital for r in reports]
    assets = [r.net_assets for r in reports]

    fig, ax = plt.subplots()
    ax.plot(years, capitals, label="Share Capital")
    ax.plot(years, assets, label="Net Assets")
    ax.set_title("Financial Trends")
    ax.set_xlabel("Year")
    ax.set_ylabel("Amount")
    ax.legend()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    return encoded
