import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from data_layer.collectors.market_collector import MarketDataCollector
from data_layer.collectors.news_collector import NewsDataCollector
from data_layer.collectors.financial_collector import FinancialDataCollector
from data_layer.storage.models import MarketData, NewsData, FinancialMetrics

def test_market_data_roundtrip(db):
    """Test market data storage and retrieval"""
    # Set date range for historical data
    end_date = datetime.now(timezone.utc) - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=7)  # Last 7 days
    
    # Store data using collect_and_store
    collector = MarketDataCollector(db)
    collector.collect_and_store(['AAPL'], '1d', start_date, end_date)
    
    # Verify data was stored
    session = db.get_session()
    try:
        # Query the stored data
        stored_data = session.query(MarketData).filter(
            MarketData.ticker == 'AAPL'
        ).all()
        
        # Verify we got at least one record
        assert len(stored_data) > 0, "Expected at least one record"
        
        # Verify the data structure
        record = stored_data[0]
        assert record.ticker == 'AAPL'
        assert isinstance(record.timestamp, datetime)
        assert record.timestamp.tzinfo == timezone.utc
        assert isinstance(record.open_price, float)
        assert isinstance(record.volume, int)
        
    finally:
        session.close()

def test_news_data_roundtrip(db):
    """Test news data storage and retrieval"""
    # Set date range for news
    end_date = datetime.now(timezone.utc) - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=7)  # Last 7 days
    
    # Store data using collect_and_store
    collector = NewsDataCollector(db)
    collector.collect_and_store(['AAPL'], start_date, end_date)
    
    # Verify data was stored
    session = db.get_session()
    try:
        # Query the stored data
        stored_data = session.query(NewsData).filter(
            NewsData.ticker == 'AAPL'
        ).all()
        
        # Verify we got at least one record
        assert len(stored_data) > 0, "Expected at least one record"
        
        # Verify the data structure
        record = stored_data[0]
        assert record.ticker == 'AAPL'
        assert isinstance(record.published_at, datetime)
        assert record.published_at.tzinfo == timezone.utc
        assert isinstance(record.sentiment_score, float)
        assert isinstance(record.title, str)
        assert isinstance(record.content, str)
        
    finally:
        session.close()

def test_financial_metrics_roundtrip(db):
    """Test financial metrics storage and retrieval"""
    # Store data using collect
    collector = FinancialDataCollector(db)
    collector.collect(['AAPL'])
    
    # Verify data was stored
    session = db.get_session()
    try:
        # Query the stored data
        stored_data = session.query(FinancialMetrics).filter(
            FinancialMetrics.ticker == 'AAPL'
        ).all()
        
        # Verify we got at least one record
        assert len(stored_data) > 0, "Expected at least one record"
        
        # Verify the data structure
        record = stored_data[0]
        assert record.ticker == 'AAPL'
        assert isinstance(record.timestamp, datetime)
        assert record.timestamp.tzinfo == timezone.utc
        
        # Verify numeric fields
        assert isinstance(record.market_cap, (int, float)) or record.market_cap is None
        assert isinstance(record.pe_ratio, (int, float)) or record.pe_ratio is None
        assert isinstance(record.profit_margin, (int, float)) or record.profit_margin is None
        
        # Verify additional_metrics is a dictionary
        assert isinstance(record.additional_metrics, dict)
        
    finally:
        session.close() 