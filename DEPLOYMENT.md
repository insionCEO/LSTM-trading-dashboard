# Deployment Guide

This guide covers both simple and production deployment options for the AI Trading System.

## 🚀 Simple Deployment (Recommended for Development)

### Prerequisites
- Python 3.11+
- pip

### Steps
1. **Clone the repository**
   ```bash
   git clone https://github.com/nreicin/ai-trading-system.git
   cd ai-trading-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Initialize database**
   ```bash
   python init_db.py
   ```

6. **Run the system**
   ```bash
   # Run simulation
   python run_january_2025_simulation.py
   
   # Start web dashboard
   python dashboard/app.py
   ```

## 🏭 Production Deployment

### Prerequisites
- Docker and Docker Compose
- API keys for data sources

### Steps

1. **Clone and configure**
   ```bash
   git clone https://github.com/nreicin/ai-trading-system.git
   cd ai-trading-system
   cp .env.example .env
   # Edit .env with production settings
   ```

2. **Start database and Redis**
   ```bash
   docker-compose up postgres redis -d
   ```

3. **Run trading system**
   ```bash
   # Option A: Run with Docker Compose
   docker-compose up trading-system
   
   # Option B: Build and run manually
   docker build -t ai-trading-system .
   docker run -p 5000:5000 --env-file .env ai-trading-system
   ```

4. **Start web dashboard** (optional)
   ```bash
   docker-compose --profile dashboard up dashboard
   ```

### Production Configuration

#### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://trader:trading123@postgres:5432/trading_system
DB_PASSWORD=trading123

# API Keys
POLYGON_API_KEY=your_polygon_key
NEWS_API_KEY=your_news_api_key
FMP_API_KEY=your_fmp_key

# Optional: Broker Integration
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
```

#### Services
- **PostgreSQL**: Database for storing market data and results
- **Redis**: Caching and message queue
- **Trading System**: Main application (port 5000)
- **Web Dashboard**: User interface (port 5001)

### Monitoring and Logs

#### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f trading-system
```

#### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U trader -d trading_system

# Backup database
docker-compose exec postgres pg_dump -U trader trading_system > backup.sql
```

#### Redis Access
```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli
```

### Scaling Considerations

#### For High Volume
- Increase PostgreSQL connection pool
- Add Redis clustering
- Use load balancer for web dashboard
- Implement proper monitoring (Prometheus/Grafana)

#### For Production Trading
- Add proper authentication
- Implement rate limiting
- Set up SSL/TLS certificates
- Configure backup strategies
- Add monitoring and alerting

### Troubleshooting

#### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps postgres
   
   # Check logs
   docker-compose logs postgres
   ```

2. **API Rate Limits**
   - Check API key configuration
   - Verify rate limiting settings
   - Monitor API usage

3. **Memory Issues**
   - Increase Docker memory limits
   - Optimize database queries
   - Monitor resource usage

#### Performance Tuning

1. **Database Optimization**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_market_data_ticker_timestamp ON market_data(ticker, timestamp);
   CREATE INDEX idx_news_data_ticker_published ON news_data(ticker, published_at);
   ```

2. **Application Tuning**
   - Adjust connection pool sizes
   - Optimize data collection intervals
   - Configure caching strategies

## 🔒 Security Considerations

### Production Checklist
- [ ] Use strong passwords for database
- [ ] Configure firewall rules
- [ ] Enable SSL/TLS
- [ ] Implement proper authentication
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
- [ ] Backup data regularly

### API Key Security
- Store API keys in environment variables
- Use secrets management in production
- Rotate keys regularly
- Monitor API usage for anomalies

## 📊 Performance Monitoring

### Key Metrics to Monitor
- Database connection pool usage
- API response times
- Memory and CPU usage
- Disk space for logs and data
- Network latency

### Recommended Tools
- **Application Monitoring**: Prometheus + Grafana
- **Log Management**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Infrastructure**: Docker stats, system monitoring

## 🚨 Emergency Procedures

### System Recovery
1. **Stop all services**
   ```bash
   docker-compose down
   ```

2. **Backup data**
   ```bash
   docker-compose exec postgres pg_dump -U trader trading_system > emergency_backup.sql
   ```

3. **Restart services**
   ```bash
   docker-compose up -d
   ```

### Data Recovery
```bash
# Restore from backup
docker-compose exec -T postgres psql -U trader -d trading_system < backup.sql
```

---

**Note**: This deployment guide covers the essential setup. For enterprise deployments, consider additional security, monitoring, and scaling requirements. 