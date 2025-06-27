"""
Historical Data Collector for Backtesting
Collects historical market, news, and financial data for simulation periods
"""
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import pandas as pd

from data_layer.storage.db_handler import DatabaseHandler
from data_layer.collectors.market_collector import MarketDataCollector
from data_layer.collectors.news_collector import NewsDataCollector
from data_layer.collectors.financial_collector import FinancialDataCollector

logger = logging.getLogger(__name__)

class HistoricalDataCollector:
    def __init__(self):
        self.db = DatabaseHandler()
        self.market_collector = MarketDataCollector(self.db)
        self.news_collector = NewsDataCollector(self.db)
        self.financial_collector = FinancialDataCollector(self.db)
        
    def collect_historical_data(self, symbols: List[str], start_date: datetime, 
                              end_date: datetime, include_news: bool = True,
                              include_financials: bool = True) -> Dict:
        """
        Collect historical data for backtesting simulation
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for data collection
            end_date: End date for data collection
            include_news: Whether to collect news data
            include_financials: Whether to collect financial data
            
        Returns:
            Dict with collection results
        """
        logger.info(f"Starting historical data collection: {start_date} to {end_date}")
        
        results = {
            'market_data': {},
            'news_data': {},
            'financial_data': {},
            'errors': [],
            'summary': {}
        }
        
        # Collect market data
        logger.info("Collecting market data...")
        market_results = self._collect_market_data(symbols, start_date, end_date)
        results['market_data'] = market_results
        
        # Collect news data if requested
        if include_news:
            logger.info("Collecting news data...")
            news_results = self._collect_news_data(symbols, start_date, end_date)
            results['news_data'] = news_results
        
        # Collect financial data if requested
        if include_financials:
            logger.info("Collecting financial data...")
            financial_results = self._collect_financial_data(symbols, start_date, end_date)
            results['financial_data'] = financial_results
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        logger.info("Historical data collection completed")
        return results
    
    def _collect_market_data(self, symbols: List[str], start_date: datetime, 
                           end_date: datetime) -> Dict:
        """Collect historical market data"""
        results = {
            'collected': [],
            'errors': [],
            'total_records': 0
        }
        
        for symbol in symbols:
            try:
                logger.info(f"Collecting market data for {symbol}")
                
                # Collect daily data for the entire period
                self.market_collector.collect_and_store(
                    [symbol], '1d', start_date, end_date
                )
                
                # Also collect some intraday data for more granular analysis
                # Collect 5-minute data for the last 30 days of the period
                intraday_start = end_date - timedelta(days=30)
                if intraday_start > start_date:
                    self.market_collector.collect_and_store(
                        [symbol], '5m', intraday_start, end_date
                    )
                
                # Verify data was collected
                market_data = self.db.get_market_data(symbol, limit=10)
                if not market_data.empty:
                    results['collected'].append(symbol)
                    results['total_records'] += len(market_data)
                    logger.info(f"Collected {len(market_data)} market records for {symbol}")
                else:
                    results['errors'].append(f"No market data collected for {symbol}")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"Error collecting market data for {symbol}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        return results
    
    def _collect_news_data(self, symbols: List[str], start_date: datetime, 
                          end_date: datetime) -> Dict:
        """Collect historical news data"""
        results = {
            'collected': [],
            'errors': [],
            'total_records': 0
        }
        
        for symbol in symbols:
            try:
                logger.info(f"Collecting news data for {symbol}")
                
                # Collect news data for the period
                self.news_collector.collect_and_store([symbol], start_date, end_date)
                
                # Verify data was collected
                news_data = self.db.get_news_sentiment(symbol, limit=10)
                if not news_data.empty:
                    results['collected'].append(symbol)
                    results['total_records'] += len(news_data)
                    logger.info(f"Collected {len(news_data)} news records for {symbol}")
                else:
                    results['errors'].append(f"No news data collected for {symbol}")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                error_msg = f"Error collecting news data for {symbol}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        return results
    
    def _collect_financial_data(self, symbols: List[str], start_date: datetime, 
                              end_date: datetime) -> Dict:
        """Collect historical financial data"""
        results = {
            'collected': [],
            'errors': [],
            'total_records': 0
        }
        
        for symbol in symbols:
            try:
                logger.info(f"Collecting financial data for {symbol}")
                
                # Collect financial data
                self.financial_collector.collect([symbol])
                
                # Verify data was collected
                financial_data = self.db.get_financial_metrics(symbol, limit=10)
                if not financial_data.empty:
                    results['collected'].append(symbol)
                    results['total_records'] += len(financial_data)
                    logger.info(f"Collected {len(financial_data)} financial records for {symbol}")
                else:
                    results['errors'].append(f"No financial data collected for {symbol}")
                
                # Rate limiting
                time.sleep(3)
                
            except Exception as e:
                error_msg = f"Error collecting financial data for {symbol}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        return results
    
    def _generate_summary(self, results: Dict) -> Dict:
        """Generate summary of data collection results"""
        summary = {
            'total_symbols': len(results['market_data'].get('collected', [])),
            'market_data_symbols': len(results['market_data'].get('collected', [])),
            'news_data_symbols': len(results['news_data'].get('collected', [])),
            'financial_data_symbols': len(results['financial_data'].get('collected', [])),
            'total_market_records': results['market_data'].get('total_records', 0),
            'total_news_records': results['news_data'].get('total_records', 0),
            'total_financial_records': results['financial_data'].get('total_records', 0),
            'total_errors': len(results['errors']),
            'success_rate': 0.0
        }
        
        # Calculate success rate
        total_attempts = summary['total_symbols'] * 3  # market, news, financial
        successful_attempts = (summary['market_data_symbols'] + 
                             summary['news_data_symbols'] + 
                             summary['financial_data_symbols'])
        
        if total_attempts > 0:
            summary['success_rate'] = (successful_attempts / total_attempts) * 100
        
        return summary
    
    def verify_data_availability(self, symbols: List[str], start_date: datetime, 
                               end_date: datetime) -> Dict:
        """Verify that sufficient data is available for backtesting"""
        verification = {
            'symbols': {},
            'overall_ready': True,
            'missing_data': []
        }
        
        for symbol in symbols:
            symbol_status = {
                'market_data': False,
                'news_data': False,
                'financial_data': False,
                'ready_for_backtest': False
            }
            
            # Check market data
            try:
                market_data = self.db.get_market_data(symbol, limit=50)
                if not market_data.empty:
                    # Check if we have data for the period
                    market_data['timestamp'] = pd.to_datetime(market_data['timestamp'])
                    period_data = market_data[
                        (market_data['timestamp'] >= start_date) & 
                        (market_data['timestamp'] <= end_date)
                    ]
                    if len(period_data) >= 10:  # At least 10 days of data
                        symbol_status['market_data'] = True
            except Exception as e:
                logger.error(f"Error checking market data for {symbol}: {e}")
            
            # Check news data
            try:
                news_data = self.db.get_news_sentiment(symbol, limit=20)
                if not news_data.empty:
                    symbol_status['news_data'] = True
            except Exception as e:
                logger.error(f"Error checking news data for {symbol}: {e}")
            
            # Check financial data
            try:
                financial_data = self.db.get_financial_metrics(symbol, limit=5)
                if not financial_data.empty:
                    symbol_status['financial_data'] = True
            except Exception as e:
                logger.error(f"Error checking financial data for {symbol}: {e}")
            
            # Determine if ready for backtest
            if symbol_status['market_data']:  # Market data is essential
                symbol_status['ready_for_backtest'] = True
            else:
                verification['overall_ready'] = False
                verification['missing_data'].append(f"{symbol}: Missing market data")
            
            verification['symbols'][symbol] = symbol_status
        
        return verification
    
    def get_data_statistics(self, symbols: List[str], start_date: datetime, 
                           end_date: datetime) -> Dict:
        """Get statistics about available data"""
        stats = {
            'symbols': {},
            'total_records': {
                'market': 0,
                'news': 0,
                'financial': 0
            }
        }
        
        for symbol in symbols:
            symbol_stats = {
                'market_records': 0,
                'news_records': 0,
                'financial_records': 0,
                'date_range': {
                    'start': None,
                    'end': None
                }
            }
            
            # Market data stats
            try:
                market_data = self.db.get_market_data(symbol, limit=1000)
                if not market_data.empty:
                    market_data['timestamp'] = pd.to_datetime(market_data['timestamp'])
                    period_data = market_data[
                        (market_data['timestamp'] >= start_date) & 
                        (market_data['timestamp'] <= end_date)
                    ]
                    symbol_stats['market_records'] = len(period_data)
                    stats['total_records']['market'] += len(period_data)
                    
                    if len(period_data) > 0:
                        symbol_stats['date_range']['start'] = period_data['timestamp'].min().isoformat()
                        symbol_stats['date_range']['end'] = period_data['timestamp'].max().isoformat()
            except Exception as e:
                logger.error(f"Error getting market stats for {symbol}: {e}")
            
            # News data stats
            try:
                news_data = self.db.get_news_sentiment(symbol, limit=1000)
                if not news_data.empty:
                    symbol_stats['news_records'] = len(news_data)
                    stats['total_records']['news'] += len(news_data)
            except Exception as e:
                logger.error(f"Error getting news stats for {symbol}: {e}")
            
            # Financial data stats
            try:
                financial_data = self.db.get_financial_metrics(symbol, limit=1000)
                if not financial_data.empty:
                    symbol_stats['financial_records'] = len(financial_data)
                    stats['total_records']['financial'] += len(financial_data)
            except Exception as e:
                logger.error(f"Error getting financial stats for {symbol}: {e}")
            
            stats['symbols'][symbol] = symbol_stats
        
        return stats 