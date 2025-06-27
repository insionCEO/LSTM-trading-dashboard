import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import logging
import pandas as pd
from datetime import datetime, timezone

from .models import Base

logger = logging.getLogger(__name__)

class DatabaseHandler:
    def __init__(self, engine=None):
        """Initialize database handler with optional engine parameter for testing"""
        if engine is None:
            # Use production database URL from environment
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL environment variable not set")
            self.engine = create_engine(db_url)
        else:
            # Use provided engine (for testing)
            self.engine = engine
            
        self.Session = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all tables defined in models."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def close(self):
        """Close the database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed") 

    def insert(self, obj):
        """Insert a single SQLAlchemy object."""
        session = self.Session()
        try:
            session.add(obj)
            session.commit()
            logger.info(f"Inserted object: {obj}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert object: {e}")
            raise
        finally:
            session.close()

    def insert_many(self, objs):
        """Insert multiple SQLAlchemy objects at once."""
        session = self.Session()
        try:
            session.add_all(objs)
            session.commit()
            logger.info(f"Inserted {len(objs)} objects.")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert objects: {e}")
            raise
        finally:
            session.close()

    def get_market_data(self, ticker: str, limit: int = 100, end_date: datetime = None) -> pd.DataFrame:
        """Get market data for a ticker."""
        try:
            query = text("""
                SELECT * FROM market_data 
                WHERE ticker = :ticker 
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            
            params = {"ticker": ticker, "limit": limit}
            if end_date:
                query = text("""
                    SELECT * FROM market_data 
                    WHERE ticker = :ticker 
                    AND timestamp <= :end_date
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """)
                params["end_date"] = end_date
            
            with self.engine.connect() as conn:
                result = conn.execute(query, params)
                data = pd.DataFrame(result.fetchall())
                
            if not data.empty:
                data.columns = result.keys()
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data.sort_values('timestamp', ascending=False, inplace=True)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting market data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def get_news_sentiment(self, ticker: str, limit: int = 50) -> pd.DataFrame:
        """Get news sentiment data for a ticker."""
        try:
            query = text("""
                SELECT * FROM news_data 
                WHERE ticker = :ticker 
                ORDER BY published_at DESC
                LIMIT :limit
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"ticker": ticker, "limit": limit})
                data = pd.DataFrame(result.fetchall())
                
            if not data.empty:
                data.columns = result.keys()
                data['published_at'] = pd.to_datetime(data['published_at'])
                data.sort_values('published_at', ascending=False, inplace=True)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting news sentiment for {ticker}: {str(e)}")
            return pd.DataFrame()

    def get_financial_metrics(self, ticker: str, limit: int = 10) -> pd.DataFrame:
        """Get financial metrics for a ticker."""
        try:
            query = text("""
                SELECT * FROM financial_metrics 
                WHERE ticker = :ticker 
                ORDER BY timestamp DESC
                LIMIT :limit
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"ticker": ticker, "limit": limit})
                data = pd.DataFrame(result.fetchall())
                
            if not data.empty:
                data.columns = result.keys()
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data.sort_values('timestamp', ascending=False, inplace=True)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting financial metrics for {ticker}: {str(e)}")
            return pd.DataFrame()
