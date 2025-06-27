import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_layer.storage.db_handler import DatabaseHandler
from data_layer.storage.models import Base, FinancialMetrics

@pytest.fixture(scope="session")
def db():
    """Create a test database with only financial metrics table"""
    # Create in-memory SQLite database for testing
    engine = create_engine('sqlite:///:memory:')
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create database handler
    db_handler = DatabaseHandler(engine=engine)
    
    yield db_handler
    
    # Cleanup
    Base.metadata.drop_all(engine) 