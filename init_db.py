import logging
from sqlalchemy import create_engine, text
from data_layer.storage.db_handler import DatabaseHandler
from data_layer.storage.models import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TABLES = [
    "market_data",
    "news_data",
    "financial_metrics"
]

def init_database():
    """Initialize the database with all required tables."""
    try:
        # Create database handler and engine
        db = DatabaseHandler()

        # Create all tables
        Base.metadata.create_all(db.engine)
        logger.info("✅ Successfully created all database tables")

        # Verify each expected table exists
        with db.get_session() as session:
            for table_name in TABLES:
                result = session.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = :table_name
                    )
                """), {"table_name": table_name}).scalar()
                if result:
                    logger.info(f"✅ Table exists: {table_name}")
                else:
                    logger.warning(f"⚠️  Table missing: {table_name}")

    except Exception as e:
        logger.error(f"❌ Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    init_database()
