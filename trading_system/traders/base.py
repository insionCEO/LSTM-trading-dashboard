from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy import text

from data_layer.storage.db_handler import DatabaseHandler

logger = logging.getLogger(__name__)

class ExecutionSimulator:
    """Simulates trade execution for testing and development."""
    
    def __init__(self):
        self.positions: Dict[str, float] = {}  # ticker -> quantity
        self.trade_history: list = []
    
    def execute(self, signal: str, ticker: str, quantity: float = 1.0) -> bool:
        """
        Simulate trade execution.
        
        Args:
            signal: "BUY" or "SELL"
            ticker: Stock ticker symbol
            quantity: Number of shares to trade
            
        Returns:
            bool: True if execution was successful
        """
        try:
            if signal == "BUY":
                self.positions[ticker] = self.positions.get(ticker, 0) + quantity
                logger.info(f"Bought {quantity} shares of {ticker}")
            elif signal == "SELL":
                current_position = self.positions.get(ticker, 0)
                if current_position >= quantity:
                    self.positions[ticker] = current_position - quantity
                    logger.info(f"Sold {quantity} shares of {ticker}")
                else:
                    logger.warning(f"Insufficient position in {ticker} for sale")
                    return False
            
            self.trade_history.append({
                'timestamp': datetime.now(timezone.utc),
                'ticker': ticker,
                'signal': signal,
                'quantity': quantity
            })
            return True
            
        except Exception as e:
            logger.error(f"Error executing {signal} for {ticker}: {str(e)}")
            return False
    
    def get_position(self, ticker: str) -> float:
        """Get current position size for a ticker."""
        return self.positions.get(ticker, 0.0)
    
    def get_trade_history(self) -> pd.DataFrame:
        """Get trade history as a DataFrame."""
        return pd.DataFrame(self.trade_history)

class Trader(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, db_handler: DatabaseHandler):
        self.db = db_handler
        self.executor = ExecutionSimulator()
        self.tickers = ['AAPL']  # Default to AAPL, can be overridden
    
    @abstractmethod
    def generate_signal(self, data: Dict[str, Any]) -> str:
        """
        Generate trading signal based on strategy logic.
        
        Args:
            data: Dictionary containing all necessary data for signal generation
            
        Returns:
            str: "BUY", "SELL", or "HOLD"
        """
        raise NotImplementedError("Implement in subclass")
    
    def get_market_data(self, ticker: str, lookback_days: int = 30) -> pd.DataFrame:
        """Get market data for a ticker."""
        try:
            query = text("""
                SELECT * FROM market_data 
                WHERE ticker = :ticker 
                AND timestamp >= :start_date
                ORDER BY timestamp DESC
            """)
            
            start_date = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - pd.Timedelta(days=lookback_days)
            
            with self.db.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"ticker": ticker, "start_date": start_date}
                )
                data = pd.DataFrame(result.fetchall())
                
            if not data.empty:
                data.columns = result.keys()
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data.set_index('timestamp', inplace=True)
                data.sort_index(inplace=True)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting market data for {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def get_financial_metrics(self, ticker: str) -> pd.DataFrame:
        """Get financial metrics for a ticker."""
        try:
            query = text("""
                SELECT * FROM financial_metrics 
                WHERE ticker = :ticker 
                ORDER BY timestamp DESC
            """)
            
            with self.db.engine.connect() as conn:
                result = conn.execute(query, {"ticker": ticker})
                data = pd.DataFrame(result.fetchall())
                
            if not data.empty:
                data.columns = result.keys()
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data.set_index('timestamp', inplace=True)
                data.sort_index(inplace=True)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting financial metrics for {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def get_news_sentiment(self, ticker: str, lookback_days: int = 7) -> pd.DataFrame:
        """Get news sentiment data for a ticker."""
        try:
            query = text("""
                SELECT * FROM news_data 
                WHERE ticker = :ticker 
                AND published_at >= :start_date
                ORDER BY published_at DESC
            """)
            
            start_date = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - pd.Timedelta(days=lookback_days)
            
            with self.db.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"ticker": ticker, "start_date": start_date}
                )
                data = pd.DataFrame(result.fetchall())
                
            if not data.empty:
                data.columns = result.keys()
                data['published_at'] = pd.to_datetime(data['published_at'])
                data.set_index('published_at', inplace=True)
                data.sort_index(inplace=True)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting news sentiment for {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def run(self):
        """Run the trading strategy for all configured tickers."""
        for ticker in self.tickers:
            try:
                # Gather all necessary data
                market_data = self.get_market_data(ticker)
                financial_metrics = self.get_financial_metrics(ticker)
                news_sentiment = self.get_news_sentiment(ticker)
                
                if market_data.empty:
                    logger.warning(f"No market data available for {ticker}")
                    continue
                
                # Generate and execute signal
                data = {
                    'market_data': market_data,
                    'financial_metrics': financial_metrics,
                    'news_sentiment': news_sentiment
                }
                
                signal = self.generate_signal(data)
                if signal != "HOLD":
                    self.executor.execute(signal, ticker)
                    
            except Exception as e:
                logger.error(f"Error running strategy for {ticker}: {str(e)}")
                continue 