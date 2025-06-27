import pytest
from sqlalchemy import inspect
from data_layer.storage.db_handler import DatabaseHandler
from data_layer.storage.models import MarketData, NewsData, FinancialMetrics

def test_all_tables_exist(db):
    """Test that all required tables exist"""
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    required_tables = {'market_data', 'news_data', 'financial_metrics'}
    assert required_tables.issubset(set(tables)), f"Missing tables. Found: {tables}, Expected: {required_tables}"

def test_market_data_columns(db):
    """Test that market_data table has all required columns"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('market_data')]
    
    # Check required columns
    required_columns = [
        'id', 'ticker', 'timestamp', 'open_price', 'high_price',
        'low_price', 'close_price', 'volume', 'interval',
        'created_at', 'updated_at'
    ]
    
    for col in required_columns:
        assert col in columns, f"Missing column: {col}"

def test_news_data_columns(db):
    """Test that news_data table has all required columns"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('news_data')]
    
    # Check required columns
    required_columns = [
        'id', 'title', 'content', 'source', 'url', 'published_at',
        'ticker', 'sentiment_score', 'created_at', 'updated_at'
    ]
    
    for col in required_columns:
        assert col in columns, f"Missing column: {col}"

def test_financial_metrics_columns(db):
    """Test that financial_metrics table has all required columns"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('financial_metrics')]
    
    # Check required columns
    required_columns = [
        'id', 'ticker', 'timestamp', 'market_cap', 'enterprise_value',
        'pe_ratio', 'forward_pe', 'peg_ratio', 'profit_margin',
        'operating_margin', 'return_on_equity', 'return_on_assets',
        'revenue_growth', 'earnings_growth', 'current_ratio',
        'debt_to_equity', 'quick_ratio', 'additional_metrics',
        'created_at', 'updated_at'
    ]
    
    for col in required_columns:
        assert col in columns, f"Missing column: {col}" 