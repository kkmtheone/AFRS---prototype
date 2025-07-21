from sqlalchemy import create_engine
from models import Base

engine = create_engine("sqlite:///./app.db") 

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("✅ Database tables recreated.")
