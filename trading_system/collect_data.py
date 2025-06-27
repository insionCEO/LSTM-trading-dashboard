import logging
from datetime import datetime, timezone, timedelta
from data_layer.collectors.market_collector import MarketDataCollector
from data_layer.collectors.news_collector import NewsDataCollector
from data_layer.collectors.financial_collector import FinancialDataCollector
from data_layer.storage.db_handler import DatabaseHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def collect_all_data(tickers: list = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']):
    """Collect data for all tables."""
    db = DatabaseHandler()
    
    # Set date range for market and news data
    now = datetime.now(timezone.utc)
    end_date = now
    start_date = end_date - timedelta(days=30)  # Collect 30 days of data
    
    logger.info(f"Current time: {now}")
    logger.info(f"Collecting data from {start_date} to {end_date}")
    
    try:
        # Collect market data
        logger.info("\nCollecting market data...")
        market_collector = MarketDataCollector(db)
        market_collector.collect_and_store(tickers, '1d', start_date, end_date)
        
        # Collect news data
        logger.info("\nCollecting news data...")
        news_collector = NewsDataCollector(db)
        news_collector.collect_and_store(tickers, start_date, end_date)
        
        # Collect financial metrics
        logger.info("\nCollecting financial metrics...")
        financial_collector = FinancialDataCollector(db)
        # Use a shorter lookback period for financial metrics
        financial_start = end_date - timedelta(days=7)
        financial_collector.collect(tickers, start_date=financial_start, end_date=end_date)
        
        logger.info("\nData collection completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during data collection: {str(e)}")
        raise

if __name__ == "__main__":
    collect_all_data() 