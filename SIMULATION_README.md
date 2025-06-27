# AI Trading System - Simulation Dashboard

## 🎯 Overview

This comprehensive trading simulation system allows you to backtest multiple AI trading strategies using historical data. The system includes:

- **Historical Data Collection** - Gather market, news, and financial data
- **Backtesting Engine** - Simulate trades with realistic conditions
- **Web Dashboard** - Interactive interface for running simulations
- **Performance Analytics** - Comprehensive metrics and visualizations
- **Strategy Comparison** - Compare multiple trading approaches

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file with your API keys:

```bash
# Data API Keys
POLYGON_API_KEY=your_polygon_api_key
NEWS_API_KEY=your_news_api_key
FMP_API_KEY=your_financial_modeling_prep_key

# Database
DATABASE_URL=postgresql://localhost/trading_system
```

### 3. Initialize Database

```bash
python init_db.py
```

### 4. Run January 2025 Simulation

```bash
python run_january_2025_simulation.py
```

### 5. Start Web Dashboard

```bash
python dashboard/app.py
```

Then open http://localhost:5001 in your browser.

## 📊 Available Trading Strategies

### 1. **Multi-Factor Strategy**
- Combines signals from all other strategies
- Uses weighted scoring system
- Most comprehensive approach

### 2. **Momentum Strategy**
- Trades based on price momentum
- Uses moving averages and RSI
- Good for trending markets

### 3. **Mean Reversion Strategy**
- Trades based on price mean reversion
- Uses Bollinger Bands and oversold/overbought indicators
- Good for range-bound markets

### 4. **Sentiment Strategy**
- Trades based on news sentiment analysis
- Analyzes news articles and social media
- Captures market sentiment shifts

### 5. **Fundamental Strategy**
- Trades based on financial metrics
- Uses P/E ratios, P/B ratios, earnings growth
- Long-term value investing approach

### 6. **Ensemble Strategy**
- Majority vote from all strategies
- Reduces individual strategy bias
- More conservative approach

## 🎮 Using the Web Dashboard

### Step 1: Configure Simulation
1. Select stock symbols (multiple selection available)
2. Set start and end dates
3. Choose initial capital amount
4. Select trading strategy
5. Set commission rate

### Step 2: Data Management
- **Verify Data**: Check if historical data is available
- **Collect Data**: Download missing historical data
- **Run Simulation**: Execute the backtest

### Step 3: Analyze Results
- **Key Metrics**: Total return, Sharpe ratio, max drawdown, win rate
- **Equity Curve**: Visual chart of portfolio performance
- **Trade History**: Detailed list of all trades
- **Performance Summary**: Capital and P&L breakdown

## 📈 Performance Metrics

### Return Metrics
- **Total Return**: Absolute percentage gain/loss
- **Annualized Return**: Yearly return rate
- **Risk-Adjusted Return**: Return per unit of risk

### Risk Metrics
- **Sharpe Ratio**: Risk-adjusted performance measure
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Volatility**: Standard deviation of returns
- **VaR (Value at Risk)**: Potential loss at confidence level

### Trading Metrics
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Average Trade**: Mean P&L per trade
- **Best/Worst Trade**: Largest gain and loss

## 🔧 Configuration Options

### Risk Management
```python
RISK_CONFIG = {
    'max_position_size': 0.1,      # 10% max per position
    'max_daily_loss': 0.05,        # 5% max daily loss
    'stop_loss_pct': 0.05,         # 5% stop loss
    'take_profit_pct': 0.15,       # 15% take profit
    'max_positions': 10            # Max concurrent positions
}
```

### Data Collection
```python
DATA_CONFIG = {
    'real_time_interval': '1m',    # 1-minute intervals
    'historical_interval': '5m',   # 5-minute for analysis
    'news_update_frequency': 15,   # News every 15 minutes
    'financial_update_frequency': 60  # Financials every hour
}
```

## 📁 Project Structure

```
├── trading_system/
│   ├── backtesting.py              # Backtesting engine
│   ├── historical_data_collector.py # Data collection
│   ├── traders/                    # Trading strategies
│   ├── risk_management.py          # Risk controls
│   └── broker_integration.py       # Real trading (future)
├── dashboard/
│   ├── app.py                      # Flask web app
│   └── templates/
│       └── index.html              # Dashboard UI
├── data_layer/                     # Data collection layer
├── simulation_results/             # Saved simulation results
├── logs/                          # Simulation logs
└── run_january_2025_simulation.py # January 2025 simulation
```

## 🎯 January 2025 Simulation

The January 2025 simulation tests all strategies on major tech stocks:

### Stocks Tested
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)
- META (Meta)
- TSLA (Tesla)
- NVDA (NVIDIA)
- NFLX (Netflix)

### Simulation Parameters
- **Period**: January 1-31, 2025
- **Initial Capital**: $100,000
- **Commission**: 0.1%
- **Data Types**: Market, news, financial metrics

### Expected Output
1. **Strategy Comparison Table** - Performance metrics for each strategy
2. **Best Strategy Identification** - Top performing approach
3. **Detailed Results File** - JSON with complete simulation data
4. **Recommendations** - Risk assessment and deployment advice

## 🔍 Interpreting Results

### Good Performance Indicators
- **Sharpe Ratio > 1.0**: Excellent risk-adjusted returns
- **Win Rate > 60%**: Consistent profitability
- **Max Drawdown < 5%**: Low risk
- **Positive Total Return**: Profitable strategy

### Warning Signs
- **Sharpe Ratio < 0.5**: Poor risk-adjusted performance
- **Win Rate < 40%**: Inconsistent results
- **Max Drawdown > 15%**: High risk
- **Negative Total Return**: Losing strategy

## 🚨 Important Notes

### Data Limitations
- Historical data availability depends on API access
- News sentiment may not be available for all periods
- Financial metrics are typically quarterly

### Simulation Assumptions
- Perfect execution (no slippage)
- Fixed commission rates
- No market impact from trades
- Historical data represents future performance

### Risk Disclaimer
- Past performance doesn't guarantee future results
- Simulations are for educational purposes
- Real trading involves additional risks
- Always test strategies thoroughly before live trading

## 🛠️ Troubleshooting

### Common Issues

1. **API Rate Limits**
   - Add delays between requests
   - Use multiple API keys
   - Implement retry logic

2. **Missing Data**
   - Check API key validity
   - Verify symbol availability
   - Use alternative data sources

3. **Database Errors**
   - Check database connection
   - Verify table structure
   - Clear corrupted data

4. **Memory Issues**
   - Reduce number of symbols
   - Use shorter time periods
   - Implement data pagination

## 📞 Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review API documentation
3. Verify configuration settings
4. Test with smaller datasets first

## 🔮 Future Enhancements

- **Real-time Trading**: Live strategy execution
- **Machine Learning**: Adaptive strategy optimization
- **Portfolio Management**: Multi-asset allocation
- **Advanced Analytics**: More sophisticated metrics
- **Mobile App**: Trading on the go

---

**Happy Trading! 📈** 