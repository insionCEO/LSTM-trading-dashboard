from newsapi import NewsApiClient
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
import os
from typing import List, Optional
from bs4 import BeautifulSoup
import re
from textblob import TextBlob
from ..storage.db_handler import DatabaseHandler
from ..storage.models import NewsData

logger = logging.getLogger(__name__)

class NewsDataCollector:
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler
        self.api_key = os.getenv('NEWS_API_KEY')
        self.news_api = NewsApiClient(api_key=self.api_key)
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.retry_delay = float(os.getenv('RETRY_DELAY', 5))
    
    def clean_text(self, text: str) -> str:
        """
        Clean and standardize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove HTML tags
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Remove emojis and special characters
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text using TextBlob.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score between -1 (negative) and 1 (positive)
        """
        try:
            # Clean the text
            cleaned_text = self.clean_text(text)
            
            # Analyze sentiment
            analysis = TextBlob(cleaned_text)
            
            # Return polarity (-1 to 1)
            return analysis.sentiment.polarity
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return 0.0
    
    def fetch_news(self, ticker: str, from_date: Optional[datetime] = None,
                  to_date: Optional[datetime] = None) -> List[dict]:
        """
        Fetch news articles for a given ticker.
        
        Args:
            ticker: Stock ticker symbol
            from_date: Start date for news
            to_date: End date for news
            
        Returns:
            List of news articles
        """
        if not from_date:
            from_date = datetime.now() - timedelta(days=1)
        if not to_date:
            to_date = datetime.now()
            
        for attempt in range(self.max_retries):
            try:
                response = self.news_api.get_everything(
                    q=ticker,
                    from_param=from_date.strftime('%Y-%m-%d'),
                    to=to_date.strftime('%Y-%m-%d'),
                    language='en',
                    sort_by='publishedAt'
                )
                
                if response['status'] != 'ok':
                    logger.error(f"News API error: {response.get('message', 'Unknown error')}")
                    return []
                
                return response['articles']
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for ticker {ticker}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
    
    def store_news_data(self, ticker: str, articles: List[dict]):
        """
        Store news articles in the database.
        
        Args:
            ticker: Stock ticker symbol
            articles: List of news articles
        """
        session = self.db_handler.get_session()
        try:
            for article in articles:
                # Clean and prepare text
                title = self.clean_text(article['title'])
                content = self.clean_text(article.get('description', ''))
                
                # Analyze sentiment
                sentiment_score = self.analyze_sentiment(f"{title} {content}")
                
                news_data = NewsData(
                    title=title,
                    content=content,
                    source=article['source']['name'],
                    url=article['url'],
                    published_at=datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00')),
                    ticker=ticker,
                    sentiment_score=sentiment_score
                )
                session.add(news_data)
            
            session.commit()
            logger.info(f"Successfully stored {len(articles)} news articles for {ticker}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to store news data for {ticker}: {str(e)}")
            raise
        finally:
            session.close()
    
    def collect_and_store(self, tickers: List[str], from_date: Optional[datetime] = None,
                         to_date: Optional[datetime] = None):
        """
        Collect and store news data for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            from_date: Start date for news
            to_date: End date for news
        """
        for ticker in tickers:
            try:
                logger.info(f"Collecting news for {ticker}")
                articles = self.fetch_news(ticker, from_date, to_date)
                if articles:
                    self.store_news_data(ticker, articles)
            except Exception as e:
                logger.error(f"Failed to process news for {ticker}: {str(e)}")
                continue 