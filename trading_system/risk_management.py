"""
Risk Management System for AI Trading
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    side: str  # 'long' or 'short'
    timestamp: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@dataclass
class PortfolioRisk:
    total_value: float
    total_pnl: float
    daily_pnl: float
    max_drawdown: float
    volatility: float
    sharpe_ratio: float
    risk_level: RiskLevel
    position_count: int
    correlation_score: float

class RiskManager:
    def __init__(self, config: Dict):
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.risk_history: List[PortfolioRisk] = []
        
        # Risk limits
        self.max_position_size = config.get('max_position_size', 0.1)
        self.max_portfolio_risk = config.get('max_portfolio_risk', 0.02)
        self.max_daily_loss = config.get('max_daily_loss', 0.05)
        self.max_drawdown = config.get('max_drawdown', 0.15)
        self.stop_loss_pct = config.get('stop_loss_pct', 0.05)
        self.take_profit_pct = config.get('take_profit_pct', 0.15)
        self.max_positions = config.get('max_positions', 10)
        
    def calculate_position_size(self, portfolio_value: float, symbol: str, 
                              price: float, volatility: float) -> float:
        """Calculate optimal position size based on risk parameters"""
        # Kelly Criterion for position sizing
        win_rate = 0.55  # Estimated win rate
        avg_win = self.take_profit_pct
        avg_loss = self.stop_loss_pct
        
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        
        # Adjust for volatility
        volatility_adjustment = 1 / (1 + volatility * 10)
        
        # Apply position size limits
        max_size = portfolio_value * self.max_position_size * volatility_adjustment
        kelly_size = portfolio_value * kelly_fraction * volatility_adjustment
        
        return min(max_size, kelly_size, portfolio_value * 0.1)
    
    def check_stop_loss_take_profit(self, symbol: str, current_price: float) -> Tuple[bool, str]:
        """Check if position should be closed due to stop loss or take profit"""
        if symbol not in self.positions:
            return False, ""
            
        position = self.positions[symbol]
        
        if position.side == 'long':
            if position.stop_loss and current_price <= position.stop_loss:
                return True, "stop_loss"
            if position.take_profit and current_price >= position.take_profit:
                return True, "take_profit"
        else:  # short
            if position.stop_loss and current_price >= position.stop_loss:
                return True, "stop_loss"
            if position.take_profit and current_price <= position.take_profit:
                return True, "take_profit"
                
        return False, ""
    
    def calculate_portfolio_risk(self, portfolio_value: float, 
                               market_data: pd.DataFrame) -> PortfolioRisk:
        """Calculate comprehensive portfolio risk metrics"""
        if not self.positions:
            return PortfolioRisk(
                total_value=portfolio_value,
                total_pnl=0.0,
                daily_pnl=0.0,
                max_drawdown=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                risk_level=RiskLevel.LOW,
                position_count=0,
                correlation_score=0.0
            )
        
        # Calculate P&L for each position
        total_pnl = 0.0
        position_values = []
        
        for symbol, position in self.positions.items():
            if position.side == 'long':
                pnl = (position.current_price - position.entry_price) * position.quantity
            else:
                pnl = (position.entry_price - position.current_price) * position.quantity
            
            total_pnl += pnl
            position_values.append(position.quantity * position.current_price)
        
        # Calculate daily P&L (simplified)
        daily_pnl = total_pnl * 0.1  # Assume 10% of total P&L is daily
        
        # Calculate volatility
        if len(position_values) > 1:
            volatility = np.std(position_values) / np.mean(position_values)
        else:
            volatility = 0.0
        
        # Calculate correlation score
        correlation_score = self._calculate_correlation_score(market_data)
        
        # Calculate max drawdown (simplified)
        max_drawdown = min(0, total_pnl / portfolio_value)
        
        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = (total_pnl / portfolio_value) / (volatility + 0.01) if volatility > 0 else 0
        
        # Determine risk level
        risk_level = self._determine_risk_level(
            daily_pnl / portfolio_value,
            max_drawdown,
            volatility,
            len(self.positions)
        )
        
        return PortfolioRisk(
            total_value=portfolio_value + total_pnl,
            total_pnl=total_pnl,
            daily_pnl=daily_pnl,
            max_drawdown=max_drawdown,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            risk_level=risk_level,
            position_count=len(self.positions),
            correlation_score=correlation_score
        )
    
    def _calculate_correlation_score(self, market_data: pd.DataFrame) -> float:
        """Calculate correlation between positions"""
        if len(self.positions) < 2:
            return 0.0
            
        symbols = list(self.positions.keys())
        if len(symbols) > 5:  # Limit to top 5 positions for performance
            symbols = symbols[:5]
            
        # Get price data for correlation calculation
        price_data = []
        for symbol in symbols:
            if symbol in market_data.columns:
                price_data.append(market_data[symbol].dropna())
        
        if len(price_data) < 2:
            return 0.0
            
        # Calculate correlation matrix
        try:
            correlation_matrix = pd.concat(price_data, axis=1).corr()
            # Return average correlation (excluding diagonal)
            correlations = []
            for i in range(len(correlation_matrix)):
                for j in range(i+1, len(correlation_matrix)):
                    correlations.append(abs(correlation_matrix.iloc[i, j]))
            
            return np.mean(correlations) if correlations else 0.0
        except:
            return 0.0
    
    def _determine_risk_level(self, daily_return: float, drawdown: float, 
                            volatility: float, position_count: int) -> RiskLevel:
        """Determine overall portfolio risk level"""
        risk_score = 0
        
        # Daily return risk
        if abs(daily_return) > self.max_daily_loss:
            risk_score += 3
        elif abs(daily_return) > self.max_daily_loss * 0.5:
            risk_score += 1
            
        # Drawdown risk
        if abs(drawdown) > self.max_drawdown:
            risk_score += 3
        elif abs(drawdown) > self.max_drawdown * 0.5:
            risk_score += 1
            
        # Volatility risk
        if volatility > 0.05:  # 5% volatility threshold
            risk_score += 2
        elif volatility > 0.03:
            risk_score += 1
            
        # Position concentration risk
        if position_count > self.max_positions:
            risk_score += 2
        elif position_count > self.max_positions * 0.8:
            risk_score += 1
            
        if risk_score >= 6:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def should_trade(self, symbol: str, signal: str, portfolio_value: float,
                    market_data: pd.DataFrame) -> Tuple[bool, str]:
        """Determine if a trade should be executed based on risk parameters"""
        # Check if we're at max positions
        if len(self.positions) >= self.max_positions and symbol not in self.positions:
            return False, "Maximum positions reached"
        
        # Calculate current portfolio risk
        portfolio_risk = self.calculate_portfolio_risk(portfolio_value, market_data)
        
        # Check risk level
        if portfolio_risk.risk_level == RiskLevel.CRITICAL:
            return False, "Critical risk level - no new trades"
        elif portfolio_risk.risk_level == RiskLevel.HIGH and signal != "SELL":
            return False, "High risk level - only closing positions"
        
        # Check daily loss limit
        if portfolio_risk.daily_pnl < -portfolio_value * self.max_daily_loss:
            return False, "Daily loss limit reached"
        
        # Check correlation
        if portfolio_risk.correlation_score > 0.7:
            return False, "High correlation risk"
        
        return True, "Trade approved"
    
    def add_position(self, symbol: str, quantity: float, entry_price: float,
                    side: str, stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None):
        """Add a new position to the risk manager"""
        # Set default stop loss and take profit if not provided
        if stop_loss is None:
            if side == 'long':
                stop_loss = entry_price * (1 - self.stop_loss_pct)
            else:
                stop_loss = entry_price * (1 + self.stop_loss_pct)
                
        if take_profit is None:
            if side == 'long':
                take_profit = entry_price * (1 + self.take_profit_pct)
            else:
                take_profit = entry_price * (1 - self.take_profit_pct)
        
        self.positions[symbol] = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            side=side,
            timestamp=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        logger.info(f"Added position: {symbol} {side} {quantity} @ {entry_price}")
    
    def update_position(self, symbol: str, current_price: float):
        """Update position with current price"""
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price
    
    def remove_position(self, symbol: str):
        """Remove a position from the risk manager"""
        if symbol in self.positions:
            del self.positions[symbol]
            logger.info(f"Removed position: {symbol}")
    
    def get_risk_report(self, portfolio_value: float, market_data: pd.DataFrame) -> Dict:
        """Generate comprehensive risk report"""
        portfolio_risk = self.calculate_portfolio_risk(portfolio_value, market_data)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'portfolio_value': portfolio_risk.total_value,
            'total_pnl': portfolio_risk.total_pnl,
            'daily_pnl': portfolio_risk.daily_pnl,
            'max_drawdown': portfolio_risk.max_drawdown,
            'volatility': portfolio_risk.volatility,
            'sharpe_ratio': portfolio_risk.sharpe_ratio,
            'risk_level': portfolio_risk.risk_level.value,
            'position_count': portfolio_risk.position_count,
            'correlation_score': portfolio_risk.correlation_score,
            'positions': [
                {
                    'symbol': pos.symbol,
                    'side': pos.side,
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'pnl': (pos.current_price - pos.entry_price) * pos.quantity if pos.side == 'long' 
                           else (pos.entry_price - pos.current_price) * pos.quantity,
                    'stop_loss': pos.stop_loss,
                    'take_profit': pos.take_profit
                }
                for pos in self.positions.values()
            ]
        } 