import logging
from datetime import datetime, timezone
from data_layer.storage.db_handler import DatabaseHandler
from trading_system.traders.trading_strategies import (
    MomentumTrader,
    MeanReversionTrader,
    SentimentTrader,
    FundamentalTrader,
    MultiFactorTrader
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_trader(trader_class, name: str, ticker: str = 'AAPL'):
    """Test a trading strategy."""
    try:
        logger.info(f"\nTesting {name} strategy...")
        db = DatabaseHandler()
        trader = trader_class(db)
        trader.tickers = [ticker]
        
        # Run the strategy
        trader.run()
        
        # Get trade history
        history = trader.executor.get_trade_history()
        if not history.empty:
            logger.info(f"\nTrade history for {name}:")
            logger.info(history)
        else:
            logger.info(f"No trades executed by {name}")
            
    except Exception as e:
        logger.error(f"Error testing {name}: {str(e)}")

def main():
    """Test all trading strategies."""
    ticker = 'AAPL'  # Test with Apple stock
    
    # Test each strategy
    test_trader(MomentumTrader, "Momentum", ticker)
    test_trader(MeanReversionTrader, "Mean Reversion", ticker)
    test_trader(SentimentTrader, "Sentiment", ticker)
    test_trader(FundamentalTrader, "Fundamental", ticker)
    test_trader(MultiFactorTrader, "Multi-Factor", ticker)

if __name__ == "__main__":
    main()
