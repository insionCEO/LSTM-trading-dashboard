"""
Trading Simulation Dashboard
Web interface for running backtests and viewing results
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import pandas as pd

from trading_system.backtesting import BacktestingEngine
from trading_system.historical_data_collector import HistoricalDataCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global variables for storing simulation results
simulation_results = {}
current_simulation_id = None

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/symbols')
def get_symbols():
    """Get available symbols for trading"""
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',
        'JPM', 'JNJ', 'PG', 'UNH', 'HD', 'MA', 'V', 'PYPL', 'BAC', 'WMT'
    ]
    return jsonify({'symbols': symbols})

@app.route('/api/strategies')
def get_strategies():
    """Get available trading strategies"""
    strategies = [
        {'id': 'multifactor', 'name': 'Multi-Factor', 'description': 'Combines all strategies'},
        {'id': 'momentum', 'name': 'Momentum', 'description': 'Trades based on price momentum'},
        {'id': 'mean_reversion', 'name': 'Mean Reversion', 'description': 'Trades based on price mean reversion'},
        {'id': 'sentiment', 'name': 'Sentiment', 'description': 'Trades based on news sentiment'},
        {'id': 'fundamental', 'name': 'Fundamental', 'description': 'Trades based on financial metrics'},
        {'id': 'ensemble', 'name': 'Ensemble', 'description': 'Majority vote from all strategies'}
    ]
    return jsonify({'strategies': strategies})

@app.route('/api/collect-data', methods=['POST'])
def collect_data():
    """Collect historical data for simulation"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        start_date = datetime.fromisoformat(data.get('start_date'))
        end_date = datetime.fromisoformat(data.get('end_date'))
        
        logger.info(f"Collecting data for {symbols} from {start_date} to {end_date}")
        
        # Initialize data collector
        collector = HistoricalDataCollector()
        
        # Collect data
        results = collector.collect_historical_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            include_news=True,
            include_financials=True
        )
        
        return jsonify({
            'success': True,
            'message': 'Data collection completed',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error collecting data: {e}")
        return jsonify({
            'success': False,
            'message': f'Error collecting data: {str(e)}'
        }), 500

@app.route('/api/verify-data', methods=['POST'])
def verify_data():
    """Verify data availability for simulation"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        start_date = datetime.fromisoformat(data.get('start_date'))
        end_date = datetime.fromisoformat(data.get('end_date'))
        
        # Initialize data collector
        collector = HistoricalDataCollector()
        
        # Verify data availability
        verification = collector.verify_data_availability(symbols, start_date, end_date)
        
        # Get data statistics
        stats = collector.get_data_statistics(symbols, start_date, end_date)
        
        return jsonify({
            'success': True,
            'verification': verification,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        return jsonify({
            'success': False,
            'message': f'Error verifying data: {str(e)}'
        }), 500

@app.route('/api/run-simulation', methods=['POST'])
def run_simulation():
    """Run trading simulation"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        start_date = datetime.fromisoformat(data.get('start_date'))
        end_date = datetime.fromisoformat(data.get('end_date'))
        initial_capital = float(data.get('initial_capital', 100000))
        strategy = data.get('strategy', 'multifactor')
        commission = float(data.get('commission', 0.001))
        
        logger.info(f"Running simulation: {strategy} strategy, ${initial_capital:,.2f} capital")
        
        # Initialize backtesting engine
        engine = BacktestingEngine(initial_capital=initial_capital)
        
        # Run backtest
        results = engine.run_backtest(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            commission=commission
        )
        
        # Store results
        global current_simulation_id
        current_simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        simulation_results[current_simulation_id] = {
            'config': {
                'symbols': symbols,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'initial_capital': initial_capital,
                'strategy': strategy,
                'commission': commission
            },
            'results': {
                'initial_capital': results.initial_capital,
                'final_capital': results.final_capital,
                'total_return': results.total_return,
                'total_return_pct': results.total_return_pct,
                'sharpe_ratio': results.sharpe_ratio,
                'max_drawdown': results.max_drawdown,
                'max_drawdown_pct': results.max_drawdown_pct,
                'win_rate': results.win_rate,
                'total_trades': results.total_trades,
                'profitable_trades': results.profitable_trades,
                'avg_trade_pnl': results.avg_trade_pnl,
                'best_trade': results.best_trade,
                'worst_trade': results.worst_trade,
                'equity_curve': results.equity_curve,
                'trades': [
                    {
                        'symbol': t.symbol,
                        'side': t.side,
                        'quantity': t.quantity,
                        'price': t.price,
                        'timestamp': t.timestamp.isoformat(),
                        'strategy': t.strategy,
                        'pnl': t.pnl,
                        'commission': t.commission
                    }
                    for t in results.trades
                ]
            }
        }
        
        return jsonify({
            'success': True,
            'simulation_id': current_simulation_id,
            'message': 'Simulation completed successfully',
            'summary': {
                'total_return_pct': results.total_return_pct,
                'sharpe_ratio': results.sharpe_ratio,
                'max_drawdown_pct': results.max_drawdown_pct,
                'win_rate': results.win_rate,
                'total_trades': results.total_trades
            }
        })
        
    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        return jsonify({
            'success': False,
            'message': f'Error running simulation: {str(e)}'
        }), 500

@app.route('/api/simulation/<simulation_id>')
def get_simulation_results(simulation_id):
    """Get simulation results"""
    if simulation_id not in simulation_results:
        return jsonify({'error': 'Simulation not found'}), 404
    
    return jsonify(simulation_results[simulation_id])

@app.route('/api/simulations')
def get_simulations():
    """Get list of all simulations"""
    simulations = []
    for sim_id, sim_data in simulation_results.items():
        simulations.append({
            'id': sim_id,
            'config': sim_data['config'],
            'summary': {
                'total_return_pct': sim_data['results']['total_return_pct'],
                'sharpe_ratio': sim_data['results']['sharpe_ratio'],
                'max_drawdown_pct': sim_data['results']['max_drawdown_pct'],
                'win_rate': sim_data['results']['win_rate'],
                'total_trades': sim_data['results']['total_trades']
            }
        })
    
    return jsonify({'simulations': simulations})

@app.route('/api/compare-simulations', methods=['POST'])
def compare_simulations():
    """Compare multiple simulations"""
    try:
        data = request.get_json()
        simulation_ids = data.get('simulation_ids', [])
        
        comparison = []
        for sim_id in simulation_ids:
            if sim_id in simulation_results:
                sim_data = simulation_results[sim_id]
                comparison.append({
                    'id': sim_id,
                    'strategy': sim_data['config']['strategy'],
                    'initial_capital': sim_data['config']['initial_capital'],
                    'total_return_pct': sim_data['results']['total_return_pct'],
                    'sharpe_ratio': sim_data['results']['sharpe_ratio'],
                    'max_drawdown_pct': sim_data['results']['max_drawdown_pct'],
                    'win_rate': sim_data['results']['win_rate'],
                    'total_trades': sim_data['results']['total_trades']
                })
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        logger.error(f"Error comparing simulations: {e}")
        return jsonify({
            'success': False,
            'message': f'Error comparing simulations: {str(e)}'
        }), 500

@app.route('/api/export-results/<simulation_id>')
def export_results(simulation_id):
    """Export simulation results as JSON"""
    if simulation_id not in simulation_results:
        return jsonify({'error': 'Simulation not found'}), 404
    
    return jsonify(simulation_results[simulation_id])

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 