"""
Backtesting Engine for AI Trading System
Simulates trading strategies using historical data
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json

from .traders import (
    MomentumTrader, MeanReversionTrader, SentimentTrader, 
    FundamentalTrader, MultiFactorTrader
)
from .risk_management import RiskManager
from data_layer.storage.db_handler import DatabaseHandler

logger = logging.getLogger(__name__)

@dataclass
class Trade:
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    timestamp: datetime
    strategy: str
    pnl: float = 0.0
    commission: float = 0.0

@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    side: str  # 'long' or 'short'
    timestamp: datetime
    unrealized_pnl: float = 0.0

@dataclass
class BacktestResult:
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    avg_trade_pnl: float
    best_trade: float
    worst_trade: float
    daily_returns: List[float]
    equity_curve: List[Dict]
    trades: List[Trade]
    positions: List[Position]
    strategy_performance: Dict[str, Dict]

class BacktestingEngine:
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve = []
        self.daily_returns = []
        
        # Initialize database and traders
        self.db = DatabaseHandler()
        self.traders = {
            'momentum': MomentumTrader(self.db),
            'mean_reversion': MeanReversionTrader(self.db),
            'sentiment': SentimentTrader(self.db),
            'fundamental': FundamentalTrader(self.db),
            'multifactor': MultiFactorTrader(self.db)
        }
        
        # Risk management
        self.risk_manager = RiskManager({
            'max_position_size': 0.1,
            'max_daily_loss': 0.05,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.15
        })
        
        # Performance tracking
        self.strategy_performance = {name: {'trades': 0, 'pnl': 0.0} for name in self.traders.keys()}
        
    def run_backtest(self, symbols: List[str], start_date: datetime, end_date: datetime,
                    strategy: str = 'multifactor', commission: float = 0.001) -> BacktestResult:
        """
        Run backtest for specified period and symbols
        """
        logger.info(f"Starting backtest: {start_date} to {end_date}, Strategy: {strategy}")
        
        # Reset state
        self._reset_state()
        
        # Get date range
        current_date = start_date
        last_equity_update = None
        
        while current_date <= end_date:
            try:
                # Skip weekends
                if current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue
                
                # Update positions with current prices
                self._update_positions(current_date)
                
                # Generate signals for all symbols
                signals = self._generate_signals(symbols, current_date, strategy)
                
                # Execute trades based on signals
                self._execute_trades(signals, current_date, commission)
                
                # Check stop losses and take profits
                self._check_position_exits(current_date, commission)
                
                # Update equity curve (daily)
                if last_equity_update is None or (current_date - last_equity_update).days >= 1:
                    self._update_equity_curve(current_date)
                    last_equity_update = current_date
                
                current_date += timedelta(days=1)
                
            except Exception as e:
                logger.error(f"Error in backtest for {current_date}: {e}")
                current_date += timedelta(days=1)
        
        # Close all positions at end
        self._close_all_positions(end_date, commission)
        
        # Calculate final results
        return self._calculate_results()
    
    def _reset_state(self):
        """Reset backtesting state"""
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.daily_returns = []
        self.strategy_performance = {name: {'trades': 0, 'pnl': 0.0} for name in self.traders.keys()}
    
    def _generate_signals(self, symbols: List[str], date: datetime, strategy: str) -> Dict[str, str]:
        """Generate trading signals for symbols on given date"""
        signals = {}
        
        for symbol in symbols:
            try:
                # Get historical data up to the current date
                market_data = self.db.get_market_data(symbol, limit=100, end_date=date)
                if market_data.empty:
                    continue
                
                # Generate signal using specified strategy
                if strategy == 'multifactor':
                    signal = self.traders['multifactor'].generate_signal(symbol)
                elif strategy in self.traders:
                    signal = self.traders[strategy].generate_signal(symbol)
                else:
                    # Combine all strategies
                    all_signals = []
                    for trader_name, trader in self.traders.items():
                        try:
                            all_signals.append(trader.generate_signal(symbol))
                        except:
                            all_signals.append('HOLD')
                    
                    # Majority vote
                    buy_count = all_signals.count('BUY')
                    sell_count = all_signals.count('SELL')
                    
                    if buy_count > sell_count:
                        signal = 'BUY'
                    elif sell_count > buy_count:
                        signal = 'SELL'
                    else:
                        signal = 'HOLD'
                
                signals[symbol] = signal
                
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                signals[symbol] = 'HOLD'
        
        return signals
    
    def _execute_trades(self, signals: Dict[str, str], date: datetime, commission: float):
        """Execute trades based on signals"""
        for symbol, signal in signals.items():
            try:
                # Get current price
                current_price = self._get_price(symbol, date)
                if not current_price:
                    continue
                
                if signal == 'BUY' and symbol not in self.positions:
                    # Check if we should buy based on risk management
                    should_trade, reason = self.risk_manager.should_trade(
                        symbol, signal, self.current_capital, pd.DataFrame()
                    )
                    
                    if should_trade:
                        self._execute_buy(symbol, current_price, date, commission)
                
                elif signal == 'SELL' and symbol in self.positions:
                    self._execute_sell(symbol, current_price, date, commission)
                
            except Exception as e:
                logger.error(f"Error executing trade for {symbol}: {e}")
    
    def _execute_buy(self, symbol: str, price: float, date: datetime, commission: float):
        """Execute a buy order"""
        # Calculate position size
        volatility = self._calculate_volatility(symbol, date)
        position_size = self.risk_manager.calculate_position_size(
            self.current_capital, symbol, price, volatility
        )
        
        if position_size <= 0:
            return
        
        # Calculate quantity
        quantity = position_size / price
        
        # Calculate commission
        trade_value = quantity * price
        trade_commission = trade_value * commission
        
        # Check if we have enough capital
        if trade_value + trade_commission > self.current_capital:
            return
        
        # Execute trade
        self.current_capital -= (trade_value + trade_commission)
        
        # Create position
        self.positions[symbol] = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            current_price=price,
            side='long',
            timestamp=date
        )
        
        # Record trade
        trade = Trade(
            symbol=symbol,
            side='buy',
            quantity=quantity,
            price=price,
            timestamp=date,
            strategy='multifactor',
            commission=trade_commission
        )
        self.trades.append(trade)
        
        logger.debug(f"BUY: {symbol} {quantity} @ {price}")
    
    def _execute_sell(self, symbol: str, price: float, date: datetime, commission: float):
        """Execute a sell order"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Calculate P&L
        pnl = (price - position.entry_price) * position.quantity
        
        # Calculate commission
        trade_value = position.quantity * price
        trade_commission = trade_value * commission
        
        # Update capital
        self.current_capital += (trade_value - trade_commission)
        
        # Record trade
        trade = Trade(
            symbol=symbol,
            side='sell',
            quantity=position.quantity,
            price=price,
            timestamp=date,
            strategy='multifactor',
            pnl=pnl,
            commission=trade_commission
        )
        self.trades.append(trade)
        
        # Remove position
        del self.positions[symbol]
        
        logger.debug(f"SELL: {symbol} {position.quantity} @ {price}, P&L: {pnl}")
    
    def _update_positions(self, date: datetime):
        """Update position prices"""
        for symbol, position in self.positions.items():
            current_price = self._get_price(symbol, date)
            if current_price:
                position.current_price = current_price
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
    
    def _check_position_exits(self, date: datetime, commission: float):
        """Check for stop loss and take profit exits"""
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            current_price = position.current_price
            
            # Check stop loss (5%)
            stop_loss = position.entry_price * 0.95
            if current_price <= stop_loss:
                self._execute_sell(symbol, current_price, date, commission)
                logger.debug(f"Stop loss triggered: {symbol}")
            
            # Check take profit (15%)
            take_profit = position.entry_price * 1.15
            if current_price >= take_profit:
                self._execute_sell(symbol, current_price, date, commission)
                logger.debug(f"Take profit triggered: {symbol}")
    
    def _close_all_positions(self, date: datetime, commission: float):
        """Close all remaining positions"""
        for symbol in list(self.positions.keys()):
            current_price = self._get_price(symbol, date)
            if current_price:
                self._execute_sell(symbol, current_price, date, commission)
    
    def _get_price(self, symbol: str, date: datetime) -> Optional[float]:
        """Get price for symbol on given date"""
        try:
            # Get market data for the specific date
            market_data = self.db.get_market_data(symbol, limit=1, end_date=date)
            if not market_data.empty:
                return float(market_data.iloc[-1]['close'])
            return None
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def _calculate_volatility(self, symbol: str, date: datetime) -> float:
        """Calculate volatility for symbol"""
        try:
            # Get 20 days of historical data
            market_data = self.db.get_market_data(symbol, limit=20, end_date=date)
            if market_data.empty:
                return 0.02
            
            returns = market_data['close'].pct_change().dropna()
            return returns.std()
        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {e}")
            return 0.02
    
    def _update_equity_curve(self, date: datetime):
        """Update equity curve with current portfolio value"""
        # Calculate current portfolio value
        portfolio_value = self.current_capital
        
        for position in self.positions.values():
            portfolio_value += position.quantity * position.current_price
        
        self.equity_curve.append({
            'date': date.isoformat(),
            'equity': portfolio_value,
            'capital': self.current_capital,
            'positions_value': portfolio_value - self.current_capital
        })
    
    def _calculate_results(self) -> BacktestResult:
        """Calculate comprehensive backtest results"""
        if not self.equity_curve:
            return self._empty_results()
        
        # Calculate basic metrics
        initial_equity = self.equity_curve[0]['equity']
        final_equity = self.equity_curve[-1]['equity']
        total_return = final_equity - initial_equity
        total_return_pct = (total_return / initial_equity) * 100
        
        # Calculate daily returns
        daily_returns = []
        for i in range(1, len(self.equity_curve)):
            prev_equity = self.equity_curve[i-1]['equity']
            curr_equity = self.equity_curve[i]['equity']
            daily_return = (curr_equity - prev_equity) / prev_equity
            daily_returns.append(daily_return)
        
        # Calculate Sharpe ratio
        if daily_returns:
            avg_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown
        max_drawdown, max_drawdown_pct = self._calculate_max_drawdown()
        
        # Calculate trade statistics
        total_trades = len(self.trades)
        profitable_trades = len([t for t in self.trades if t.pnl > 0])
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        trade_pnls = [t.pnl for t in self.trades if t.pnl != 0]
        avg_trade_pnl = np.mean(trade_pnls) if trade_pnls else 0
        best_trade = max(trade_pnls) if trade_pnls else 0
        worst_trade = min(trade_pnls) if trade_pnls else 0
        
        return BacktestResult(
            initial_capital=initial_equity,
            final_capital=final_equity,
            total_return=total_return,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            win_rate=win_rate,
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            avg_trade_pnl=avg_trade_pnl,
            best_trade=best_trade,
            worst_trade=worst_trade,
            daily_returns=daily_returns,
            equity_curve=self.equity_curve,
            trades=self.trades,
            positions=list(self.positions.values()),
            strategy_performance=self.strategy_performance
        )
    
    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum drawdown"""
        if not self.equity_curve:
            return 0.0, 0.0
        
        equity_values = [point['equity'] for point in self.equity_curve]
        peak = equity_values[0]
        max_drawdown = 0
        max_drawdown_pct = 0
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            drawdown = peak - equity
            drawdown_pct = (drawdown / peak) * 100
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
        
        return max_drawdown, max_drawdown_pct
    
    def _empty_results(self) -> BacktestResult:
        """Return empty results when no data"""
        return BacktestResult(
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            total_return=0.0,
            total_return_pct=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            max_drawdown_pct=0.0,
            win_rate=0.0,
            total_trades=0,
            profitable_trades=0,
            avg_trade_pnl=0.0,
            best_trade=0.0,
            worst_trade=0.0,
            daily_returns=[],
            equity_curve=[],
            trades=[],
            positions=[],
            strategy_performance=self.strategy_performance
        ) 