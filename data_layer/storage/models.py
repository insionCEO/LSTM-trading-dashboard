from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, JSON, Text
from sqlalchemy.types import TypeDecorator, DateTime as SA_DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TZDateTime(TypeDecorator):
    """Store UTC-naïve datetimes in SQLite, but always return them as UTC-aware."""
    impl = SA_DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=timezone.utc) if value is not None else value

# ────────────────────────────────────────────────────────────────────────────────
# Market Data

class MarketData(Base):
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, index=True, nullable=False)
    timestamp = Column(TZDateTime(), nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    interval = Column(String, nullable=False)  # e.g., '1d', '1h', '5m'

    def __repr__(self):
        return f"<MarketData(ticker={self.ticker!r}, timestamp={self.timestamp!r})>"

# ────────────────────────────────────────────────────────────────────────────────
# News Data

class NewsData(Base):
    __tablename__ = 'news_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    url = Column(String, nullable=False)
    published_at = Column(TZDateTime(), nullable=False)
    ticker = Column(String, index=True, nullable=False)
    sentiment_score = Column(Float, nullable=True)

    def __repr__(self):
        return f"<NewsData(ticker={self.ticker!r}, title={self.title!r})>"

# ────────────────────────────────────────────────────────────────────────────────
# Financial Metrics

class FinancialMetrics(Base):
    __tablename__ = 'financial_metrics'

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    ticker             = Column(String, index=True, nullable=False)
    timestamp          = Column(TZDateTime(), nullable=False)

    # Core financials
    revenue            = Column(Float, nullable=True)
    net_income         = Column(Float, nullable=True)
    eps                = Column(Float, nullable=True)
    market_cap         = Column(Float, nullable=True)

    # Valuation ratios
    pe_ratio           = Column(Float, nullable=True)
    forward_pe         = Column(Float, nullable=True)
    pb_ratio           = Column(Float, nullable=True)
    peg_ratio          = Column(Float, nullable=True)

    # Margins
    profit_margin      = Column(Float, nullable=True)
    operating_margin   = Column(Float, nullable=True)

    # Return ratios
    return_on_equity   = Column(Float, nullable=True)
    return_on_assets   = Column(Float, nullable=True)

    # Growth
    revenue_growth     = Column(Float, nullable=True)
    earnings_growth    = Column(Float, nullable=True)

    # Liquidity
    current_ratio      = Column(Float, nullable=True)
    quick_ratio        = Column(Float, nullable=True)
    debt_to_equity     = Column(Float, nullable=True)

    # Raw dump of other unsupported values
    additional_metrics = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<FinancialMetrics(ticker={self.ticker!r}, timestamp={self.timestamp!r})>"
