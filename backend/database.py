from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL - adjust it according to your database settings
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Example with SQLite, change for other databases

# Create a database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})  # Add arguments for SQLite if used

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for defining models
Base = declarative_base()

# Dependency to get the database session in your routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
