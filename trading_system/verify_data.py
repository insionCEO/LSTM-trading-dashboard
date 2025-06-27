import logging
from datetime import datetime, timezone
from data_layer.storage.db_handler import DatabaseHandler
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_table_data(db, table_name: str):
    """Verify data in a specific table."""
    try:
        query = text(f"SELECT COUNT(*) as count FROM {table_name}")
        with db.engine.connect() as conn:
            result = conn.execute(query)
            count = result.scalar()
            logger.info(f"\n=== {table_name} Summary ===")
            logger.info(f"Total records: {count}")
            
            if count > 0:
                # Get sample data
                sample_query = text(f"SELECT * FROM {table_name} LIMIT 1")
                sample = conn.execute(sample_query)
                columns = sample.keys()
                logger.info(f"Columns: {', '.join(columns)}")
                
                # Get date range
                date_col = 'timestamp' if table_name != 'news_data' else 'published_at'
                range_query = text(f"""
                    SELECT MIN({date_col}) as min_date, MAX({date_col}) as max_date 
                    FROM {table_name}
                """)
                date_range = conn.execute(range_query).fetchone()
                logger.info(f"Date range: {date_range.min_date} to {date_range.max_date}")
                
    except Exception as e:
        logger.error(f"Error verifying {table_name}: {str(e)}")

def main():
    """Verify data in all tables."""
    db = DatabaseHandler()
    
    # Verify each table
    verify_table_data(db, 'market_data')
    verify_table_data(db, 'news_data')
    verify_table_data(db, 'financial_metrics')

if __name__ == "__main__":
    main() 