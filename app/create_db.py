from sqlalchemy import create_engine
from models import Base

engine = create_engine("sqlite:///./app.db")  # Adjust path if needed

# Drop all old tables and recreate them with the new structure
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("✅ Database tables recreated.")
