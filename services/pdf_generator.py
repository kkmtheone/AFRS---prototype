import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt

UPLOAD_DIR = "uploads"
CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

def generate_compliance_chart(report, company_id, year):
    """
    Creates a simple bar chart of key figures and saves it as PNG.
    Returns the chart file path.
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ['Share Capital', 'Liquid Capital', 'Net Assets', 'Liabilities']
    values = [
        report.share_capital or 0,
        report.liquid_capital or 0,
        report.net_assets or 0,
        report.total_liabilities or 0
    ]

    ax.bar(labels, values, color=['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728'])
    ax.set_title(f"Financials for {year}")
    ax.set_ylabel("Amount")

    for i, v in enumerate(values):
        ax.text(i, v + max(values) * 0.01, f"{v:,.0f}", ha='center', fontsize=8)

    chart_path = os.path.join(CHARTS_DIR, f"{company_id}_{year}.png")
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close(fig)

    return chart_path

def build_review_pdf(company, report, type_checks, solvency_ratio):
    """
    Builds a PDF review report using ReportLab and embedded compliance chart.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, f"{company.name} - {report.year} Financial Review")

    y = height - 80
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Company Type: {company.company_type.title()}")
    y -= 20

    if company.company_type.lower() == "issuer" and company.market_segment:
        pdf.drawString(50, y, f"Market Segment: {company.market_segment}")
        y -= 20

    pdf.line(50, y, width - 50, y)
    y -= 20

    # Compliance thresholds
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Regulatory Thresholds:")
    y -= 20
    pdf.setFont("Helvetica", 11)

    for key, val in type_checks.items():
        pdf.drawString(70, y, f"{key.replace('_', ' ').title()}: {val:,.0f}")
        y -= 15

    y -= 10
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Reported Figures:")
    y -= 20
    pdf.setFont("Helvetica", 11)

    pdf.drawString(70, y, f"Share Capital: {report.share_capital:,.0f}")
    y -= 15
    pdf.drawString(70, y, f"Liquid Capital: {report.liquid_capital:,.0f}")
    y -= 15
    pdf.drawString(70, y, f"Net Assets: {report.net_assets:,.0f}")
    y -= 15
    pdf.drawString(70, y, f"Total Liabilities: {report.total_liabilities:,.0f}")
    y -= 15

    y -= 10
    pdf.drawString(50, y, f"Solvency Ratio: {solvency_ratio:.2f}")
    y -= 20

    pdf.drawString(50, y, f"Submission Requirements Met: {'Yes' if report.submission_requirements_met else 'No'}")
    y -= 15
    pdf.drawString(50, y, f"Publication Requirements Met: {'Yes' if report.publication_requirements_met else 'No'}")
    y -= 30

    # Insert chart image
    chart_path = generate_compliance_chart(report, company.id, report.year)

    try:
        img = ImageReader(chart_path)
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width)

        # Fit chart nicely on page
        chart_width = width - 100
        chart_height = chart_width * aspect

        if chart_height > y - 50:
            chart_height = y - 50
            chart_width = chart_height / aspect

        pdf.drawImage(img, 50, y - chart_height, width=chart_width, height=chart_height, preserveAspectRatio=True)

    except Exception as e:
        pdf.drawString(50, y, f"Error embedding chart: {e}")

    # Finalize PDF
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer
