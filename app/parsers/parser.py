import os
from app.models import SessionLocal, ParsedFile

def parse_file(file_path: str):
    filename = os.path.basename(file_path)
    parsed_message = f"Parsed file {filename} successfully!"

    db = SessionLocal()
    parsed = ParsedFile(
        filename=filename,
        parsed_message=parsed_message
    )
    db.add(parsed)
    db.commit()
    db.refresh(parsed)
    db.close()

    return {
        "file": filename,
        "message": parsed_message
    }
