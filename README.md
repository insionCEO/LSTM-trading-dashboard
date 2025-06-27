# AI Trading System - Simulation Dashboard

A comprehensive AI-powered trading system with historical data collection, backtesting engine, and web dashboard for strategy evaluation.

## 🚀 Overview

This system provides:
- **Historical Data Collection**: Market, news, and financial data from multiple APIs
- **Backtesting Engine**: Test trading strategies with realistic simulations
- **Web Dashboard**: Interactive interface for running simulations and analyzing results
- **Multiple Strategies**: Momentum, mean reversion, sentiment, fundamental, and ensemble approaches
- **Performance Analytics**: Sharpe ratio, drawdown analysis, win rates, and more
- **Risk Management**: Position sizing, stop-losses, and portfolio management

## ⚠️ Important Note: API Limitations

This project is designed to work with **free tier API access**. Due to API limitations, some features may require paid subscriptions for full functionality:

- **Polygon.io**: Free tier has limited historical data access
- **News API**: Free tier has rate limits and limited historical data
- **Financial Modeling Prep**: Free tier has limited API calls per day
- **Yahoo Finance**: Free but has rate limits

The system gracefully handles these limitations with:
- Rate limiting and retry logic
- Fallback data when APIs are unavailable
- Clear logging of API issues
- Stub data generation for testing

**For production use**, consider upgrading to paid API tiers or implementing alternative data sources.

## 🚀 Quick Start

### Option 1: Simple Setup (Recommended for Beginners)

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Set Up Environment Variables
Create a `.env` file with your API keys:
```bash
# Required for data collection
POLYGON_API_KEY=your_polygon_key
NEWS_API_KEY=your_news_api_key
FMP_API_KEY=your_fmp_key

# Database configuration (SQLite for simple setup)
DATABASE_URL=sqlite:///trading_system.db
```

#### 3. Initialize Database
```bash
python init_db.py
```

#### 4. Run January 2025 Simulation
```bash
python run_january_2025_simulation.py
```

#### 5. Start Web Dashboard
```bash
python dashboard/app.py
```
Then visit http://localhost:5001

### Option 2: Production Setup (Advanced)

For production deployment with PostgreSQL, Redis, and containerization:

#### 1. Install Docker and Docker Compose
```bash
# Install Docker Desktop or Docker Engine
# Install Docker Compose
```

#### 2. Set Up Environment Variables
Create a `.env` file with production settings:
```bash
# Database
DATABASE_URL=postgresql://trader:trading123@localhost:5432/trading_system
DB_PASSWORD=trading123

# API Keys
POLYGON_API_KEY=your_polygon_key
NEWS_API_KEY=your_news_api_key
FMP_API_KEY=your_fmp_key

# Optional: Broker Integration
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
```

#### 3. Start Production Services
```bash
# Start database and Redis
docker-compose up postgres redis -d

# Run the trading system
docker-compose up trading-system

# Optional: Start web dashboard
docker-compose --profile dashboard up dashboard
```

#### 4. Access Services
- **Web Dashboard**: http://localhost:5001
- **Trading System**: http://localhost:5000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 📊 Available Trading Strategies

### 1. **Multi-Factor Strategy**
Combines all other strategies using weighted scoring to generate signals.

### 2. **Momentum Strategy**
Uses price momentum indicators (RSI, MACD) to identify trending stocks.

### 3. **Mean Reversion Strategy**
Identifies overbought/oversold conditions using moving averages and Bollinger Bands.

### 4. **Sentiment Strategy**
Analyzes news sentiment to predict price movements based on market sentiment.

### 5. **Fundamental Strategy**
Uses financial ratios (P/E, P/B, ROE) to identify undervalued stocks.

### 6. **Ensemble Strategy**
Combines signals from multiple strategies using majority voting.

## 🎯 Using the Web Dashboard

### Configuration
1. **Stock Symbols**: Enter comma-separated ticker symbols (e.g., AAPL,MSFT,GOOGL)
2. **Date Range**: Select start and end dates for simulation
3. **Initial Capital**: Set starting investment amount
4. **Trading Strategy**: Choose from available strategies
5. **Commission Rate**: Set trading commission percentage

### Running Simulations
1. Click "Verify Data" to check data availability
2. Click "Collect Data" to gather fresh market data
3. Click "Run Simulation" to execute backtesting
4. View results in the performance dashboard

### Key Metrics
- **Total Return**: Overall percentage gain/loss
- **Sharpe Ratio**: Risk-adjusted performance measure
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Trade History**: Detailed list of all trades
- **Equity Curve**: Portfolio value over time

## 🏗️ Project Structure

```
├── data_layer/                 # Data collection and storage
│   ├── collectors/            # API data collectors
│   ├── storage/              # Database models and handler
│   └── pipeline/             # Data processing pipeline
├── trading_system/           # Core trading logic
│   ├── traders/             # Trading strategies
│   ├── backtesting.py       # Backtesting engine
│   └── risk_management.py   # Risk management
├── dashboard/               # Web interface
│   ├── templates/          # HTML templates
│   └── app.py             # Flask application
├── tests/                  # Test suite
├── logs/                   # Application logs
├── simulation_results/     # Backtesting results
├── docker-compose.yml      # Production services
├── production_config.py    # Production configuration
└── run_trading_system.py   # Production launcher
```

## 📈 Performance Metrics

The system calculates comprehensive performance metrics:

- **Total Return**: Overall portfolio performance
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest portfolio decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Average Trade**: Mean profit/loss per trade
- **Best/Worst Trade**: Individual trade extremes

## ⚙️ Configuration Options

### Environment Variables
- `DATABASE_URL`: Database connection string
- `POLYGON_API_KEY`: Market data API key
- `NEWS_API_KEY`: News sentiment API key
- `FMP_API_KEY`: Financial metrics API key

### Trading Parameters
- **Position Sizing**: Percentage of capital per trade
- **Stop Loss**: Maximum loss per position
- **Take Profit**: Target profit levels
- **Commission Rate**: Trading costs
- **Risk Per Trade**: Maximum risk per position

## 🔧 Development

### Running Tests
```bash
python -m pytest tests/
```

### Data Verification
```bash
python trading_system/verify_data.py
```

### Manual Data Collection
```bash
python trading_system/collect_data.py
```

### Production Deployment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f trading-system

# Stop services
docker-compose down
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📞 Support

For questions or issues:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information

---

**Note**: This is a simulation system for educational and research purposes. Always test strategies thoroughly before using real money. 