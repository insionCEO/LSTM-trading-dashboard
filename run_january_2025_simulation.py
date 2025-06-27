#!/usr/bin/env python3
"""
January 2025 Trading Simulation
Runs a comprehensive backtest for January 2025 with all trading strategies
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

from trading_system.backtesting import BacktestingEngine
from trading_system.historical_data_collector import HistoricalDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/january_2025_simulation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_january_2025_simulation():
    """Run comprehensive simulation for January 2025"""
    
    # Configuration
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX']
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 1, 31)
    initial_capital = 100000
    commission = 0.001  # 0.1%
    
    strategies = [
        'multifactor',
        'momentum', 
        'mean_reversion',
        'sentiment',
        'fundamental',
        'ensemble'
    ]
    
    logger.info("=== January 2025 Trading Simulation ===")
    logger.info(f"Symbols: {symbols}")
    logger.info(f"Period: {start_date.date()} to {end_date.date()}")
    logger.info(f"Initial Capital: ${initial_capital:,.2f}")
    logger.info(f"Commission: {commission*100}%")
    
    # Step 1: Collect Historical Data
    logger.info("\n=== Step 1: Collecting Historical Data ===")
    collector = HistoricalDataCollector()
    
    try:
        collection_results = collector.collect_historical_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            include_news=True,
            include_financials=True
        )
        
        logger.info("Data collection completed:")
        logger.info(f"  Market data: {collection_results['summary']['market_data_symbols']} symbols")
        logger.info(f"  News data: {collection_results['summary']['news_data_symbols']} symbols")
        logger.info(f"  Financial data: {collection_results['summary']['financial_data_symbols']} symbols")
        logger.info(f"  Success rate: {collection_results['summary']['success_rate']:.1f}%")
        
    except Exception as e:
        logger.error(f"Error collecting data: {e}")
        return
    
    # Step 2: Verify Data Availability
    logger.info("\n=== Step 2: Verifying Data Availability ===")
    try:
        verification = collector.verify_data_availability(symbols, start_date, end_date)
        
        if verification['overall_ready']:
            logger.info("✅ Data verification successful - ready for simulation")
        else:
            logger.warning("⚠️ Some data missing:")
            for missing in verification['missing_data']:
                logger.warning(f"  - {missing}")
            
            # Continue anyway with available data
            logger.info("Proceeding with available data...")
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        return
    
    # Step 3: Run Simulations for Each Strategy
    logger.info("\n=== Step 3: Running Strategy Simulations ===")
    
    results = {}
    
    for strategy in strategies:
        logger.info(f"\n--- Testing {strategy.upper()} Strategy ---")
        
        try:
            # Initialize backtesting engine
            engine = BacktestingEngine(initial_capital=initial_capital)
            
            # Run backtest
            backtest_results = engine.run_backtest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                strategy=strategy,
                commission=commission
            )
            
            # Store results
            results[strategy] = {
                'initial_capital': backtest_results.initial_capital,
                'final_capital': backtest_results.final_capital,
                'total_return': backtest_results.total_return,
                'total_return_pct': backtest_results.total_return_pct,
                'sharpe_ratio': backtest_results.sharpe_ratio,
                'max_drawdown': backtest_results.max_drawdown,
                'max_drawdown_pct': backtest_results.max_drawdown_pct,
                'win_rate': backtest_results.win_rate,
                'total_trades': backtest_results.total_trades,
                'profitable_trades': backtest_results.profitable_trades,
                'avg_trade_pnl': backtest_results.avg_trade_pnl,
                'best_trade': backtest_results.best_trade,
                'worst_trade': backtest_results.worst_trade
            }
            
            # Log results
            logger.info(f"  Total Return: {backtest_results.total_return_pct:.2f}%")
            logger.info(f"  Sharpe Ratio: {backtest_results.sharpe_ratio:.2f}")
            logger.info(f"  Max Drawdown: {backtest_results.max_drawdown_pct:.2f}%")
            logger.info(f"  Win Rate: {backtest_results.win_rate:.1f}%")
            logger.info(f"  Total Trades: {backtest_results.total_trades}")
            logger.info(f"  Final Capital: ${backtest_results.final_capital:,.2f}")
            
        except Exception as e:
            logger.error(f"Error running {strategy} strategy: {e}")
            results[strategy] = None
    
    # Step 4: Generate Comparison Report
    logger.info("\n=== Step 4: Strategy Comparison ===")
    
    # Create comparison table
    logger.info("\nStrategy Performance Summary:")
    logger.info("-" * 100)
    logger.info(f"{'Strategy':<15} {'Return %':<10} {'Sharpe':<8} {'Drawdown %':<12} {'Win Rate %':<12} {'Trades':<8}")
    logger.info("-" * 100)
    
    best_strategy = None
    best_return = -float('inf')
    
    for strategy, result in results.items():
        if result is not None:
            logger.info(f"{strategy:<15} {result['total_return_pct']:<10.2f} {result['sharpe_ratio']:<8.2f} "
                       f"{result['max_drawdown_pct']:<12.2f} {result['win_rate']:<12.1f} {result['total_trades']:<8}")
            
            if result['total_return_pct'] > best_return:
                best_return = result['total_return_pct']
                best_strategy = strategy
        else:
            logger.info(f"{strategy:<15} {'ERROR':<10} {'ERROR':<8} {'ERROR':<12} {'ERROR':<12} {'ERROR':<8}")
    
    logger.info("-" * 100)
    
    if best_strategy:
        logger.info(f"\n🏆 Best Performing Strategy: {best_strategy.upper()}")
        logger.info(f"   Total Return: {results[best_strategy]['total_return_pct']:.2f}%")
        logger.info(f"   Final Capital: ${results[best_strategy]['final_capital']:,.2f}")
    
    # Step 5: Save Results
    logger.info("\n=== Step 5: Saving Results ===")
    
    # Create results directory if it doesn't exist
    os.makedirs('simulation_results', exist_ok=True)
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'simulation_results/january_2025_simulation_{timestamp}.json'
    
    simulation_summary = {
        'metadata': {
            'simulation_name': 'January 2025 Trading Simulation',
            'timestamp': datetime.now().isoformat(),
            'symbols': symbols,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'initial_capital': initial_capital,
            'commission': commission
        },
        'results': results,
        'best_strategy': best_strategy,
        'collection_results': collection_results
    }
    
    with open(results_file, 'w') as f:
        json.dump(simulation_summary, f, indent=2)
    
    logger.info(f"Results saved to: {results_file}")
    
    # Step 6: Generate Recommendations
    logger.info("\n=== Step 6: Recommendations ===")
    
    if best_strategy:
        best_result = results[best_strategy]
        
        logger.info(f"Based on January 2025 simulation results:")
        logger.info(f"1. Best Strategy: {best_strategy.upper()}")
        logger.info(f"2. Expected Return: {best_result['total_return_pct']:.2f}% per month")
        logger.info(f"3. Risk Level: {'Low' if best_result['max_drawdown_pct'] < 5 else 'Medium' if best_result['max_drawdown_pct'] < 10 else 'High'}")
        logger.info(f"4. Consistency: {'High' if best_result['win_rate'] > 60 else 'Medium' if best_result['win_rate'] > 50 else 'Low'}")
        
        if best_result['sharpe_ratio'] > 1.0:
            logger.info("5. Risk-Adjusted Performance: Excellent (Sharpe > 1.0)")
        elif best_result['sharpe_ratio'] > 0.5:
            logger.info("5. Risk-Adjusted Performance: Good (Sharpe > 0.5)")
        else:
            logger.info("5. Risk-Adjusted Performance: Poor (Sharpe < 0.5)")
    
    logger.info("\n=== Simulation Complete ===")
    logger.info("Check the web dashboard for detailed visualizations and trade analysis.")

if __name__ == "__main__":
    run_january_2025_simulation() 