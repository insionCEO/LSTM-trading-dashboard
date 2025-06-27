#!/usr/bin/env python3
"""
Production Trading System Launcher
"""
import os
import sys
import logging
import signal
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from production_config import (
    TRADING_CONFIG, DATA_CONFIG, RISK_CONFIG, 
    BROKER_CONFIG, DB_CONFIG, LOGGING_CONFIG
)
from trading_system.trading_engine import TradingEngine

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=getattr(logging, LOGGING_CONFIG['level']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOGGING_CONFIG['file']),
            logging.StreamHandler(sys.stdout)
        ]
    )

class TradingSystem:
    def __init__(self):
        self.engine = None
        self.running = False
        
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        
    def start(self):
        """Start the trading system"""
        try:
            self.logger.info("Starting AI Trading System...")
            
            # Validate configuration
            self._validate_config()
            
            # Create configuration for trading engine
            config = {
                'enabled': TRADING_CONFIG['enabled'],
                'paper_trading': TRADING_CONFIG['paper_trading'],
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX'],
                'risk_config': RISK_CONFIG,
                'broker_config': BROKER_CONFIG,
                'close_positions_on_stop': True
            }
            
            # Initialize trading engine
            self.engine = TradingEngine(config)
            
            # Start the engine
            self.engine.start()
            self.running = True
            
            self.logger.info("Trading system started successfully")
            
            # Main loop
            while self.running:
                try:
                    # Get status
                    status = self.engine.get_status()
                    
                    # Log status every 5 minutes
                    if datetime.now().minute % 5 == 0 and datetime.now().second < 10:
                        self.logger.info(f"Status: {status}")
                        
                        # Log performance summary
                        performance = self.engine.get_performance_summary()
                        if performance:
                            self.logger.info(f"Performance: {performance}")
                    
                    time.sleep(10)
                    
                except KeyboardInterrupt:
                    self.logger.info("Received keyboard interrupt")
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    time.sleep(30)
                    
        except Exception as e:
            self.logger.error(f"Error starting trading system: {e}")
            self.stop()
            
    def stop(self):
        """Stop the trading system"""
        if not self.running:
            return
            
        self.logger.info("Stopping trading system...")
        self.running = False
        
        if self.engine:
            self.engine.stop()
            
        self.logger.info("Trading system stopped")
        
    def _validate_config(self):
        """Validate configuration"""
        # Check required environment variables
        required_vars = ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        # Check database connection
        try:
            from data_layer.storage.db_handler import DatabaseHandler
            db = DatabaseHandler()
            db.create_tables()
            self.logger.info("Database connection validated")
        except Exception as e:
            raise ValueError(f"Database connection failed: {e}")
        
        # Check broker connection
        try:
            from trading_system.broker_integration import AlpacaBroker
            broker = AlpacaBroker(BROKER_CONFIG)
            account = broker.get_account()
            self.logger.info(f"Broker connection validated - Account: {account.get('id', 'Unknown')}")
        except Exception as e:
            raise ValueError(f"Broker connection failed: {e}")

def main():
    """Main entry point"""
    trading_system = TradingSystem()
    
    try:
        trading_system.start()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        trading_system.stop()

if __name__ == "__main__":
    main() 