"""
Production Trading Engine for AI Trading System
Integrates data collection, strategy execution, risk management, and broker integration
"""
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from .traders import (
    MomentumTrader, MeanReversionTrader, SentimentTrader, 
    FundamentalTrader, MultiFactorTrader
)
from .risk_management import RiskManager
from .broker_integration import AlpacaBroker, Order
from data_layer.storage.db_handler import DatabaseHandler
from data_layer.collectors.market_collector import MarketDataCollector
from data_layer.collectors.news_collector import NewsDataCollector
from data_layer.collectors.financial_collector import FinancialDataCollector

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.running = False
        self.trading_enabled = config.get('enabled', False)
        self.paper_trading = config.get('paper_trading', True)
        
        # Initialize components
        self.db = DatabaseHandler()
        self.risk_manager = RiskManager(config.get('risk_config', {}))
        self.broker = AlpacaBroker(config.get('broker_config', {}))
        
        # Initialize traders
        self.traders = {
            'momentum': MomentumTrader(self.db),
            'mean_reversion': MeanReversionTrader(self.db),
            'sentiment': SentimentTrader(self.db),
            'fundamental': FundamentalTrader(self.db),
            'multifactor': MultiFactorTrader(self.db)
        }
        
        # Initialize data collectors
        self.market_collector = MarketDataCollector(self.db)
        self.news_collector = NewsDataCollector(self.db)
        self.financial_collector = FinancialDataCollector(self.db)
        
        # Trading state
        self.symbols = config.get('symbols', ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'])
        self.portfolio_value = 0.0
        self.last_signal_check = None
        self.signal_cooldown = 300  # 5 minutes between signal checks
        
        # Performance tracking
        self.performance_history = []
        self.trade_history = []
        
        logger.info("Trading engine initialized")
    
    def start(self):
        """Start the trading engine"""
        if self.running:
            logger.warning("Trading engine is already running")
            return
        
        self.running = True
        logger.info("Starting trading engine...")
        
        # Start data collection thread
        self.data_thread = threading.Thread(target=self._data_collection_loop, daemon=True)
        self.data_thread.start()
        
        # Start trading loop
        self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.trading_thread.start()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Trading engine started successfully")
    
    def stop(self):
        """Stop the trading engine"""
        if not self.running:
            logger.warning("Trading engine is not running")
            return
        
        logger.info("Stopping trading engine...")
        self.running = False
        
        # Close all positions if configured
        if self.config.get('close_positions_on_stop', False):
            self.broker.close_all_positions()
        
        logger.info("Trading engine stopped")
    
    def _data_collection_loop(self):
        """Continuous data collection loop"""
        while self.running:
            try:
                # Check if market is open
                if not self.broker.is_market_open():
                    logger.debug("Market is closed, skipping data collection")
                    time.sleep(60)
                    continue
                
                # Collect market data
                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(minutes=15)
                
                self.market_collector.collect_and_store(
                    self.symbols, '5m', start_date, end_date
                )
                
                # Collect news data (less frequently)
                if datetime.now().minute % 15 == 0:  # Every 15 minutes
                    self.news_collector.collect_and_store(
                        self.symbols, start_date, end_date
                    )
                
                # Collect financial data (daily)
                if datetime.now().hour == 8 and datetime.now().minute == 0:
                    self.financial_collector.collect(self.symbols)
                
                time.sleep(60)  # Wait 1 minute before next collection
                
            except Exception as e:
                logger.error(f"Error in data collection loop: {e}")
                time.sleep(60)
    
    def _trading_loop(self):
        """Main trading loop"""
        while self.running:
            try:
                # Check if market is open
                if not self.broker.is_market_open():
                    logger.debug("Market is closed, skipping trading")
                    time.sleep(60)
                    continue
                
                # Check if enough time has passed since last signal check
                now = datetime.now()
                if (self.last_signal_check and 
                    (now - self.last_signal_check).seconds < self.signal_cooldown):
                    time.sleep(30)
                    continue
                
                # Update portfolio value
                self._update_portfolio_value()
                
                # Generate trading signals
                signals = self._generate_signals()
                
                # Execute trades based on signals
                self._execute_trades(signals)
                
                self.last_signal_check = now
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(60)
    
    def _monitoring_loop(self):
        """Monitoring and risk management loop"""
        while self.running:
            try:
                # Update portfolio risk metrics
                self._update_risk_metrics()
                
                # Check for stop loss/take profit
                self._check_position_exits()
                
                # Generate performance report
                self._update_performance()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _update_portfolio_value(self):
        """Update current portfolio value"""
        try:
            account = self.broker.get_account()
            self.portfolio_value = account.get('portfolio_value', 0)
        except Exception as e:
            logger.error(f"Error updating portfolio value: {e}")
    
    def _generate_signals(self) -> Dict[str, Dict]:
        """Generate trading signals for all symbols"""
        signals = {}
        
        for symbol in self.symbols:
            try:
                # Get market data
                market_data = self.db.get_market_data(symbol, limit=100)
                if market_data.empty:
                    continue
                
                # Get news sentiment
                sentiment_data = self.db.get_news_sentiment(symbol, limit=50)
                
                # Get financial metrics
                financial_data = self.db.get_financial_metrics(symbol, limit=10)
                
                symbol_signals = {}
                
                # Generate signals from each trader
                for name, trader in self.traders.items():
                    try:
                        signal = trader.generate_signal(symbol)
                        symbol_signals[name] = signal
                    except Exception as e:
                        logger.error(f"Error generating {name} signal for {symbol}: {e}")
                        symbol_signals[name] = "HOLD"
                
                signals[symbol] = symbol_signals
                
            except Exception as e:
                logger.error(f"Error generating signals for {symbol}: {e}")
        
        return signals
    
    def _execute_trades(self, signals: Dict[str, Dict]):
        """Execute trades based on signals"""
        for symbol, symbol_signals in signals.items():
            try:
                # Use multifactor signal as primary decision
                primary_signal = symbol_signals.get('multifactor', 'HOLD')
                
                # Check if we should trade based on risk management
                should_trade, reason = self.risk_manager.should_trade(
                    symbol, primary_signal, self.portfolio_value, pd.DataFrame()
                )
                
                if not should_trade:
                    logger.debug(f"Trade rejected for {symbol}: {reason}")
                    continue
                
                # Get current price
                current_price = self.broker.get_latest_price(symbol)
                if not current_price:
                    continue
                
                # Execute trade based on signal
                if primary_signal == "BUY":
                    self._execute_buy_order(symbol, current_price)
                elif primary_signal == "SELL":
                    self._execute_sell_order(symbol, current_price)
                
            except Exception as e:
                logger.error(f"Error executing trades for {symbol}: {e}")
    
    def _execute_buy_order(self, symbol: str, price: float):
        """Execute a buy order"""
        try:
            # Calculate position size
            volatility = self._calculate_volatility(symbol)
            position_size = self.risk_manager.calculate_position_size(
                self.portfolio_value, symbol, price, volatility
            )
            
            if position_size <= 0:
                return
            
            # Calculate quantity
            quantity = position_size / price
            
            # Place order
            order = Order(
                symbol=symbol,
                quantity=quantity,
                side='buy',
                order_type='market',
                time_in_force='day'
            )
            
            order_id = self.broker.place_order(order)
            if order_id:
                # Add position to risk manager
                self.risk_manager.add_position(
                    symbol, quantity, price, 'long'
                )
                
                logger.info(f"Executed BUY order: {symbol} {quantity} @ {price}")
                
        except Exception as e:
            logger.error(f"Error executing buy order for {symbol}: {e}")
    
    def _execute_sell_order(self, symbol: str, price: float):
        """Execute a sell order"""
        try:
            # Check if we have a position to sell
            if symbol not in self.risk_manager.positions:
                return
            
            position = self.risk_manager.positions[symbol]
            
            # Place order
            order = Order(
                symbol=symbol,
                quantity=position.quantity,
                side='sell',
                order_type='market',
                time_in_force='day'
            )
            
            order_id = self.broker.place_order(order)
            if order_id:
                # Remove position from risk manager
                self.risk_manager.remove_position(symbol)
                
                logger.info(f"Executed SELL order: {symbol} {position.quantity} @ {price}")
                
        except Exception as e:
            logger.error(f"Error executing sell order for {symbol}: {e}")
    
    def _calculate_volatility(self, symbol: str) -> float:
        """Calculate volatility for a symbol"""
        try:
            market_data = self.db.get_market_data(symbol, limit=20)
            if market_data.empty:
                return 0.02  # Default volatility
            
            returns = market_data['close'].pct_change().dropna()
            return returns.std()
        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {e}")
            return 0.02
    
    def _update_risk_metrics(self):
        """Update risk metrics"""
        try:
            # Get current market data
            market_data = pd.DataFrame()  # Simplified for now
            
            # Update risk manager with current prices
            for symbol in self.symbols:
                current_price = self.broker.get_latest_price(symbol)
                if current_price:
                    self.risk_manager.update_position(symbol, current_price)
            
            # Calculate portfolio risk
            portfolio_risk = self.risk_manager.calculate_portfolio_risk(
                self.portfolio_value, market_data
            )
            
            # Log risk level
            if portfolio_risk.risk_level.value in ['high', 'critical']:
                logger.warning(f"High risk level: {portfolio_risk.risk_level.value}")
                
        except Exception as e:
            logger.error(f"Error updating risk metrics: {e}")
    
    def _check_position_exits(self):
        """Check for stop loss and take profit exits"""
        try:
            for symbol in list(self.risk_manager.positions.keys()):
                current_price = self.broker.get_latest_price(symbol)
                if not current_price:
                    continue
                
                should_exit, reason = self.risk_manager.check_stop_loss_take_profit(
                    symbol, current_price
                )
                
                if should_exit:
                    self._execute_sell_order(symbol, current_price)
                    logger.info(f"Position exit triggered for {symbol}: {reason}")
                    
        except Exception as e:
            logger.error(f"Error checking position exits: {e}")
    
    def _update_performance(self):
        """Update performance tracking"""
        try:
            # Get portfolio summary
            summary = self.broker.get_portfolio_summary()
            
            # Get risk report
            risk_report = self.risk_manager.get_risk_report(
                self.portfolio_value, pd.DataFrame()
            )
            
            # Combine performance data
            performance = {
                'timestamp': datetime.now().isoformat(),
                'portfolio_value': summary.get('total_value', 0),
                'total_pnl': summary.get('total_pnl', 0),
                'cash': summary.get('cash', 0),
                'position_count': summary.get('position_count', 0),
                'risk_level': risk_report.get('risk_level', 'low'),
                'sharpe_ratio': risk_report.get('sharpe_ratio', 0),
                'max_drawdown': risk_report.get('max_drawdown', 0)
            }
            
            self.performance_history.append(performance)
            
            # Keep only last 1000 records
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]
                
        except Exception as e:
            logger.error(f"Error updating performance: {e}")
    
    def get_status(self) -> Dict:
        """Get current trading engine status"""
        return {
            'running': self.running,
            'trading_enabled': self.trading_enabled,
            'paper_trading': self.paper_trading,
            'portfolio_value': self.portfolio_value,
            'symbols': self.symbols,
            'market_open': self.broker.is_market_open(),
            'position_count': len(self.risk_manager.positions),
            'last_signal_check': self.last_signal_check.isoformat() if self.last_signal_check else None
        }
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        if not self.performance_history:
            return {}
        
        df = pd.DataFrame(self.performance_history)
        
        return {
            'current_value': df['portfolio_value'].iloc[-1] if len(df) > 0 else 0,
            'total_return': ((df['portfolio_value'].iloc[-1] / df['portfolio_value'].iloc[0]) - 1) if len(df) > 1 else 0,
            'max_drawdown': df['max_drawdown'].min() if len(df) > 0 else 0,
            'avg_sharpe': df['sharpe_ratio'].mean() if len(df) > 0 else 0,
            'current_risk_level': df['risk_level'].iloc[-1] if len(df) > 0 else 'low',
            'data_points': len(df)
        } 