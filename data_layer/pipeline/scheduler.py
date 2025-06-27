import schedule
import time
import logging
from datetime import datetime, timedelta
from ..collectors.market_collector import MarketDataCollector
from ..collectors.news_collector import NewsDataCollector
from ..storage.db_handler import DatabaseHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# List of tickers to track
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

def collect_market_data():
    """Collect market data for all tickers."""
    try:
        logger.info("Starting market data collection")
        db_handler = DatabaseHandler()
        collector = MarketDataCollector(db_handler)
        
        # Collect daily data
        collector.collect_and_store(
            tickers=TICKERS,
            interval='1d',
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        # Collect intraday data (5-minute intervals)
        collector.collect_and_store(
            tickers=TICKERS,
            interval='5m',
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now()
        )
        
        logger.info("Market data collection completed successfully")
    except Exception as e:
        logger.error(f"Error in market data collection: {str(e)}")

def collect_news_data():
    """Collect news data for all tickers."""
    try:
        logger.info("Starting news data collection")
        db_handler = DatabaseHandler()
        collector = NewsDataCollector(db_handler)
        
        collector.collect_and_store(
            tickers=TICKERS,
            from_date=datetime.now() - timedelta(hours=1),
            to_date=datetime.now()
        )
        
        logger.info("News data collection completed successfully")
    except Exception as e:
        logger.error(f"Error in news data collection: {str(e)}")

def run_scheduler():
    """Run the data collection scheduler."""
    # Schedule market data collection (daily at market close)
    schedule.every().day.at("16:00").do(collect_market_data)
    
    # Schedule intraday market data collection (every 5 minutes during market hours)
    schedule.every(5).minutes.do(collect_market_data)
    
    # Schedule news data collection (every hour)
    schedule.every().hour.do(collect_news_data)
    
    logger.info("Scheduler started")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    run_scheduler() 