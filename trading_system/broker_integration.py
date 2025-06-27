"""
Broker Integration for AI Trading System
Supports Alpaca for paper and live trading
"""
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST
from alpaca_trade_api.stream import Stream

logger = logging.getLogger(__name__)

@dataclass
class Order:
    symbol: str
    quantity: float
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market', 'limit', 'stop', 'stop_limit'
    time_in_force: str  # 'day', 'gtc', 'ioc', 'fok'
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    client_order_id: Optional[str] = None

@dataclass
class Position:
    symbol: str
    quantity: float
    side: str  # 'long' or 'short'
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_plpc: float

class AlpacaBroker:
    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.base_url = config.get('base_url')
        self.data_url = config.get('data_url')
        self.paper_trading = config.get('paper_trading', True)
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API credentials not provided")
        
        # Initialize REST API
        self.api = REST(
            key=self.api_key,
            secret=self.api_secret,
            base_url=self.base_url,
            api_version='v2'
        )
        
        # Initialize streaming API
        self.stream = Stream(
            key=self.api_key,
            secret=self.api_secret,
            base_url=self.base_url,
            data_feed='iex'  # or 'sip' for live trading
        )
        
        # Set up streaming handlers
        self._setup_stream_handlers()
        
        logger.info(f"Initialized Alpaca broker (paper trading: {self.paper_trading})")
    
    def _setup_stream_handlers(self):
        """Set up streaming data handlers"""
        @self.stream.on('trade')
        async def handle_trade(trade):
            logger.debug(f"Trade: {trade}")
        
        @self.stream.on('quote')
        async def handle_quote(quote):
            logger.debug(f"Quote: {quote}")
        
        @self.stream.on('bar')
        async def handle_bar(bar):
            logger.debug(f"Bar: {bar}")
    
    def get_account(self) -> Dict:
        """Get account information"""
        try:
            account = self.api.get_account()
            return {
                'id': account.id,
                'status': account.status,
                'currency': account.currency,
                'buying_power': float(account.buying_power),
                'regt_buying_power': float(account.regt_buying_power),
                'daytrading_buying_power': float(account.daytrading_buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'pattern_day_trader': account.pattern_day_trader,
                'trading_blocked': account.trading_blocked,
                'transfers_blocked': account.transfers_blocked,
                'account_blocked': account.account_blocked,
                'created_at': account.created_at.isoformat(),
                'trade_suspended_by_user': account.trade_suspended_by_user,
                'multiplier': account.multiplier,
                'shorting_enabled': account.shorting_enabled,
                'equity': float(account.equity),
                'last_equity': float(account.last_equity),
                'long_market_value': float(account.long_market_value),
                'short_market_value': float(account.short_market_value),
                'initial_margin': float(account.initial_margin),
                'maintenance_margin': float(account.maintenance_margin),
                'last_maintenance_margin': float(account.last_maintenance_margin),
                'sma': float(account.sma),
                'daytrade_count': account.daytrade_count
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            positions = self.api.list_positions()
            return [
                Position(
                    symbol=pos.symbol,
                    quantity=float(pos.qty),
                    side='long' if float(pos.qty) > 0 else 'short',
                    entry_price=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                    market_value=float(pos.market_value),
                    unrealized_pl=float(pos.unrealized_pl),
                    unrealized_plpc=float(pos.unrealized_plpc)
                )
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(self, status: str = 'open') -> List[Dict]:
        """Get orders by status"""
        try:
            orders = self.api.list_orders(status=status)
            return [
                {
                    'id': order.id,
                    'symbol': order.symbol,
                    'quantity': float(order.qty),
                    'side': order.side,
                    'type': order.type,
                    'status': order.status,
                    'filled_at': order.filled_at.isoformat() if order.filled_at else None,
                    'created_at': order.created_at.isoformat(),
                    'limit_price': float(order.limit_price) if order.limit_price else None,
                    'stop_price': float(order.stop_price) if order.stop_price else None,
                    'filled_qty': float(order.filled_qty),
                    'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def place_order(self, order: Order) -> Optional[str]:
        """Place an order and return order ID"""
        try:
            # Prepare order parameters
            order_params = {
                'symbol': order.symbol,
                'qty': order.quantity,
                'side': order.side,
                'type': order.order_type,
                'time_in_force': order.time_in_force
            }
            
            if order.limit_price:
                order_params['limit_price'] = order.limit_price
            if order.stop_price:
                order_params['stop_price'] = order.stop_price
            if order.client_order_id:
                order_params['client_order_id'] = order.client_order_id
            
            # Place the order
            submitted_order = self.api.submit_order(**order_params)
            
            logger.info(f"Placed order: {order.symbol} {order.side} {order.quantity} @ {order.order_type}")
            return submitted_order.id
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            self.api.cancel_order(order_id)
            logger.info(f"Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_market_data(self, symbols: List[str], timeframe: str = '1Min', 
                       limit: int = 100) -> Dict[str, List]:
        """Get market data for symbols"""
        try:
            data = {}
            for symbol in symbols:
                bars = self.api.get_bars(symbol, timeframe, limit=limit)
                data[symbol] = [
                    {
                        'timestamp': bar.t.isoformat(),
                        'open': float(bar.o),
                        'high': float(bar.h),
                        'low': float(bar.l),
                        'close': float(bar.c),
                        'volume': int(bar.v)
                    }
                    for bar in bars
                ]
            return data
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol"""
        try:
            bars = self.api.get_bars(symbol, '1Min', limit=1)
            if bars:
                return float(bars[0].c)
            return None
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {e}")
            return None
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            clock = self.api.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Error checking market status: {e}")
            return False
    
    def get_market_hours(self) -> Dict:
        """Get market hours information"""
        try:
            clock = self.api.get_clock()
            return {
                'is_open': clock.is_open,
                'next_open': clock.next_open.isoformat() if clock.next_open else None,
                'next_close': clock.next_close.isoformat() if clock.next_close else None,
                'timestamp': clock.timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting market hours: {e}")
            return {}
    
    def start_streaming(self, symbols: List[str]):
        """Start streaming data for symbols"""
        try:
            self.stream.subscribe_trades(self._handle_trade, *symbols)
            self.stream.subscribe_quotes(self._handle_quote, *symbols)
            self.stream.subscribe_bars(self._handle_bar, *symbols)
            self.stream.run()
        except Exception as e:
            logger.error(f"Error starting streaming: {e}")
    
    def stop_streaming(self):
        """Stop streaming data"""
        try:
            self.stream.stop()
        except Exception as e:
            logger.error(f"Error stopping streaming: {e}")
    
    def _handle_trade(self, trade):
        """Handle incoming trade data"""
        logger.debug(f"Trade: {trade.symbol} @ {trade.price} x {trade.size}")
    
    def _handle_quote(self, quote):
        """Handle incoming quote data"""
        logger.debug(f"Quote: {quote.symbol} bid: {quote.bid} ask: {quote.ask}")
    
    def _handle_bar(self, bar):
        """Handle incoming bar data"""
        logger.debug(f"Bar: {bar.symbol} O:{bar.o} H:{bar.h} L:{bar.l} C:{bar.c} V:{bar.v}")
    
    def close_all_positions(self) -> bool:
        """Close all open positions"""
        try:
            positions = self.get_positions()
            for position in positions:
                side = 'sell' if position.side == 'long' else 'buy'
                order = Order(
                    symbol=position.symbol,
                    quantity=abs(position.quantity),
                    side=side,
                    order_type='market',
                    time_in_force='day'
                )
                self.place_order(order)
            
            logger.info(f"Closed {len(positions)} positions")
            return True
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
            return False
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        try:
            account = self.get_account()
            positions = self.get_positions()
            
            total_value = account.get('portfolio_value', 0)
            total_pnl = sum(pos.unrealized_pl for pos in positions)
            
            return {
                'total_value': total_value,
                'cash': account.get('cash', 0),
                'buying_power': account.get('buying_power', 0),
                'total_pnl': total_pnl,
                'position_count': len(positions),
                'positions': [
                    {
                        'symbol': pos.symbol,
                        'side': pos.side,
                        'quantity': pos.quantity,
                        'market_value': pos.market_value,
                        'unrealized_pl': pos.unrealized_pl,
                        'unrealized_plpc': pos.unrealized_plpc
                    }
                    for pos in positions
                ]
            }
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {} 