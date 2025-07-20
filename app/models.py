from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    company_type = Column(String)
    market_segment = Column(String, nullable=True)  # Only for issuers

    #reports = relationship("FinancialReport", back_populates="company")
    financial_reports = relationship("FinancialReport", back_populates="company")


class FinancialReport(Base):
    __tablename__ = "financial_reports"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    year = Column(Integer)
    share_capital = Column(Float)
    liquid_capital = Column(Float)
    net_assets = Column(Float)
    total_liabilities = Column(Float)
    submission_requirements_met = Column(Boolean)
    publication_requirements_met = Column(Boolean)
    # file_path = Column(String) if I store PDF path

    company = relationship("Company", back_populates="financial_reports")
