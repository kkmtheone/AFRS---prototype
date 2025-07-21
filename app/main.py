from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os
from sqlalchemy.orm import joinedload
from services.pdf_generator import build_review_pdf
from services.extraction import extract_numbers_from_pdf
from .database import SessionLocal, engine, Base
from .models import Company, FinancialReport

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/add_company")
def add_company_form(request: Request):
    return templates.TemplateResponse("add_company.html", {"request": request})

@app.post("/add_company")
def add_company(
    name: str = Form(...),
    company_type: str = Form(...),
    market_segment: str = Form(None),
    db: Session = Depends(get_db)
):
    company = Company(
        name=name,
        company_type=company_type,
        market_segment=market_segment if company_type.lower() == "issuer" else None,
    )
    db.add(company)
    db.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/companies")
def all_companies(request: Request, db: Session = Depends(get_db)):
    companies = db.query(Company).all()
    return templates.TemplateResponse("companies.html", {"request": request, "companies": companies})

@app.get("/pending_reviews")
def pending_reviews(request: Request, db: Session = Depends(get_db)):
    current_year = datetime.now().year
    companies = (
        db.query(Company)
        .filter(~Company.financial_reports.any(FinancialReport.year == current_year))
        .all()
    )
    return templates.TemplateResponse("pending_reviews.html", {"request": request, "companies": companies})

@app.get("/reviewed_companies")
def reviewed_companies(request: Request, db: Session = Depends(get_db)):
    current_year = datetime.now().year
    companies = (
        db.query(Company)
        .join(FinancialReport)
        .filter(FinancialReport.year == current_year)
        .all()
    )
    return templates.TemplateResponse("reviewed_companies.html", {"request": request, "companies": companies})

@app.get("/company/{company_id}")
def company_detail(company_id: int, request: Request, db: Session = Depends(get_db)):
    company = db.query(Company).options(joinedload(Company.financial_reports)).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return templates.TemplateResponse("company_detail.html", {"request": request, "company": company})

@app.get("/add_report/{company_id}")
def add_report_form(company_id: int, request: Request, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return templates.TemplateResponse("add_report.html", {"request": request, "company": company})

@app.post("/add_report/{company_id}")
async def add_report(
    company_id: int,
    year: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    file_ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{company_id}_{year}{file_ext}")

    file_bytes = await file.read()
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    extracted = extract_numbers_from_pdf(file_bytes)

    if not extracted or not extracted.get("share_capital"):
        raise HTTPException(status_code=400, detail="Could not extract financial data. Please check the PDF.")

    report = FinancialReport(
        company_id=company_id,
        year=year,
        share_capital=extracted["share_capital"] or 0,
        liquid_capital=extracted["liquid_capital"] or 0,
        net_assets=extracted["net_assets"] or 0,
        total_liabilities=extracted["total_liabilities"] or 0,
        submission_requirements_met=True,
        publication_requirements_met=True
    )
    db.add(report)
    db.commit()

    return RedirectResponse(f"/company/{company_id}", status_code=303)

@app.get("/review/{company_id}/{year}")
def develop_review(company_id: int, year: int, request: Request, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    report = db.query(FinancialReport).filter(
        FinancialReport.company_id == company_id, FinancialReport.year == year
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    type_checks = {}
    if company.company_type.lower() == "stockbroker":
        type_checks["share_capital_req"] = 50_000_000
        type_checks["liquid_capital_req"] = max(30_000_000, 0.08 * report.total_liabilities)
    elif company.company_type.lower() == "fund manager":
        type_checks["share_capital_req"] = 10_000_000
        type_checks["liquid_capital_req"] = max(5_000_000, 0.08 * report.total_liabilities)
    elif company.company_type.lower() == "investment bank":
        type_checks["share_capital_req"] = 250_000_000
        type_checks["liquid_capital_req"] = max(30_000_000, 0.08 * report.total_liabilities)
    elif company.company_type.lower() == "issuer":
        if company.market_segment == "MIMS":
            type_checks["share_capital_req"] = 50_000_000
            type_checks["net_assets_req"] = 100_000_000
        elif company.market_segment == "AIMS":
            type_checks["share_capital_req"] = 20_000_000
            type_checks["net_assets_req"] = 20_000_000
        elif company.market_segment == "GEMS":
            type_checks["share_capital_req"] = 10_000_000
            type_checks["net_assets_req"] = 100_000

    solvency_ratio = (
        report.net_assets / report.total_liabilities if report.total_liabilities else None
    )

    return templates.TemplateResponse(
        "review.html",
        {
            "request": request,
            "company": company,
            "report": report,
            "type_checks": type_checks,
            "solvency_ratio": solvency_ratio,
        },
    )

@app.get("/download_review/{company_id}/{year}")
def download_review(company_id: int, year: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    report = db.query(FinancialReport).filter(
        FinancialReport.company_id == company_id, FinancialReport.year == year
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    type_checks = {}
    if company.company_type.lower() == "stockbroker":
        type_checks["share_capital_req"] = 50_000_000
        type_checks["liquid_capital_req"] = max(30_000_000, 0.08 * report.total_liabilities)
    elif company.company_type.lower() == "fund manager":
        type_checks["share_capital_req"] = 10_000_000
        type_checks["liquid_capital_req"] = max(5_000_000, 0.08 * report.total_liabilities)
    elif company.company_type.lower() == "investment bank":
        type_checks["share_capital_req"] = 250_000_000
        type_checks["liquid_capital_req"] = max(30_000_000, 0.08 * report.total_liabilities)
    elif company.company_type.lower() == "issuer":
        if company.market_segment == "MIMS":
            type_checks["share_capital_req"] = 50_000_000
            type_checks["net_assets_req"] = 100_000_000
        elif company.market_segment == "AIMS":
            type_checks["share_capital_req"] = 20_000_000
            type_checks["net_assets_req"] = 20_000_000
        elif company.market_segment == "GEMS":
            type_checks["share_capital_req"] = 10_000_000
            type_checks["net_assets_req"] = 100_000

    solvency_ratio = (
        report.net_assets / report.total_liabilities if report.total_liabilities else 0
    )

    pdf_bytes = build_review_pdf(company, report, type_checks, solvency_ratio)

    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={company.name}_{year}_Review.pdf"}
    )

@app.post("/delete_report/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(FinancialReport).filter(FinancialReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = os.path.join(UPLOAD_DIR, f"{report.company_id}_{report.year}.pdf")
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(report)
    db.commit()

    return RedirectResponse(f"/company/{report.company_id}", status_code=303)

@app.post("/complete_review/{company_id}/{year}")
def complete_review(
    company_id: int,
    year: int,
    submission_requirements_met: bool = Form(False),
    publication_requirements_met: bool = Form(False),
    db: Session = Depends(get_db)
):
    report = db.query(FinancialReport).filter(
        FinancialReport.company_id == company_id,
        FinancialReport.year == year
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.submission_requirements_met = submission_requirements_met
    report.publication_requirements_met = publication_requirements_met
    db.commit()

    return RedirectResponse(f"/company/{company_id}", status_code=303)
