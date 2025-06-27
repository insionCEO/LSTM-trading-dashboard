"""
Production configuration for the AI Trading System
"""
import os
from datetime import time
from typing import List, Dict, Any

# Trading Configuration
TRADING_CONFIG = {
    'enabled': True,
    'paper_trading': True,  # Start with paper trading
    'max_position_size': 0.1,  # 10% of portfolio per position
    'max_portfolio_risk': 0.02,  # 2% max portfolio risk
    'stop_loss_pct': 0.05,  # 5% stop loss
    'take_profit_pct': 0.15,  # 15% take profit
    'max_positions': 10,  # Maximum concurrent positions
}

# Data Collection Configuration
DATA_CONFIG = {
    'real_time_interval': '1m',  # 1-minute intervals for real-time
    'historical_interval': '5m',  # 5-minute for historical analysis
    'news_update_frequency': 15,  # minutes
    'financial_update_frequency': 60,  # minutes
    'market_hours': {
        'start': time(9, 30),  # 9:30 AM EST
        'end': time(16, 0),    # 4:00 PM EST
    }
}

# Risk Management Configuration
RISK_CONFIG = {
    'max_daily_loss': 0.05,  # 5% max daily loss
    'max_drawdown': 0.15,    # 15% max drawdown
    'volatility_threshold': 0.03,  # 3% volatility threshold
    'correlation_threshold': 0.7,  # 70% correlation threshold
}

# Broker Configuration (for real trading)
BROKER_CONFIG = {
    'broker': 'alpaca',  # or 'interactive_brokers', 'td_ameritrade'
    'api_key': os.getenv('ALPACA_API_KEY'),
    'api_secret': os.getenv('ALPACA_SECRET_KEY'),
    'base_url': 'https://paper-api.alpaca.markets',  # Use paper trading URL
    'data_url': 'https://data.alpaca.markets',
}

# Database Configuration
DB_CONFIG = {
    'url': os.getenv('DATABASE_URL', 'postgresql://localhost/trading_system'),
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'file': 'logs/trading_system.log',
    'max_size': 100 * 1024 * 1024,  # 100MB
    'backup_count': 5,
}

# Performance Tracking
PERFORMANCE_CONFIG = {
    'track_metrics': True,
    'calculate_sharpe_ratio': True,
    'calculate_max_drawdown': True,
    'benchmark_symbol': 'SPY',  # S&P 500 ETF
} 