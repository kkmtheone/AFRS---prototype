from app.models import ParsedStatement, RedFlag
from sqlalchemy.orm import Session

def run_red_flag_checks(report_id: int, db: Session):
    """
    Runs simple red flag checks on parsed statements.
    """

    # Fetch all parsed statements for this report
    statements = db.query(ParsedStatement).filter(ParsedStatement.report_id == report_id).all()

    flags = []

    for stmt in statements:
        # EXAMPLE 1: Revenue < 0
        if stmt.statement_type == "Income Statement" and "Revenue" in stmt.line_item:
            if stmt.amount < 0:
                flags.append({
                    "description": "Revenue is negative — possible error or loss",
                    "severity": "High"
                })

        # EXAMPLE 2: Expenses unusually high (> Revenue)
        if stmt.statement_type == "Income Statement" and "Expenses" in stmt.line_item:
            # Try to find revenue for this report
            revenue = next((s for s in statements if "Revenue" in s.line_item), None)
            if revenue and stmt.amount > revenue.amount:
                flags.append({
                    "description": "Expenses exceed Revenue — check financial health",
                    "severity": "Medium"
                })

        # EXAMPLE 3: Total Assets < 0
        if stmt.statement_type == "Balance Sheet" and "Total Assets" in stmt.line_item:
            if stmt.amount < 0:
                flags.append({
                    "description": "Negative Total Assets — possible insolvency",
                    "severity": "High"
                })

    # Save flags to DB
    for flag in flags:
        db_flag = RedFlag(
            report_id=report_id,
            description=flag["description"],
            severity=flag["severity"]
        )
        db.add(db_flag)

    db.commit()
    return flags
