import logging
import pandas as pd
from typing import Dict, Any
from data_layer.storage.db_handler import DatabaseHandler
from trading_system.traders.base import Trader
from trading_system.traders.base import ExecutionSimulator


logger = logging.getLogger(__name__)

class FundamentalTrader(Trader):
    def __init__(self, db_handler: DatabaseHandler, pe_threshold_low=20.0, pe_threshold_high=35.0, growth_threshold=0.05):
        super().__init__(db_handler)
        self.pe_threshold_low = pe_threshold_low
        self.pe_threshold_high = pe_threshold_high
        self.growth_threshold = growth_threshold

    def generate_signal(self, data: Dict[str, Any]) -> str:
        try:
            metrics = data['financial_metrics']
            if metrics.empty:
                logger.info("No financial metrics available.")
                return "HOLD"

            latest = metrics.iloc[0]
            pe = latest.get("pe_ratio")
            rev_growth = latest.get("revenue_growth")
            earn_growth = latest.get("earnings_growth")

            logger.info(f"Fundamental data: PE={pe}, Revenue Growth={rev_growth}, Earnings Growth={earn_growth}")

            if pd.isna(pe) or pd.isna(rev_growth) or pd.isna(earn_growth):
                return "HOLD"

            if pe < self.pe_threshold_low and rev_growth > self.growth_threshold and earn_growth > self.growth_threshold:
                return "BUY"
            elif pe > self.pe_threshold_high:
                return "SELL"

            return "HOLD"
        except Exception as e:
            logger.error(f"Error generating fundamental signal: {str(e)}")
            return "HOLD"

class SentimentTrader(Trader):
    def __init__(self, db_handler: DatabaseHandler, sentiment_threshold=0.3, min_articles=2):
        super().__init__(db_handler)
        self.sentiment_threshold = sentiment_threshold
        self.min_articles = min_articles

    def generate_signal(self, data: Dict[str, Any]) -> str:
        try:
            sentiment = data['news_sentiment']
            if sentiment.empty or len(sentiment) < self.min_articles:
                logger.info("Not enough news sentiment data.")
                return "HOLD"

            avg = sentiment['sentiment_score'].mean()
            logger.info(f"Avg sentiment score: {avg}")

            if avg > self.sentiment_threshold:
                return "BUY"
            elif avg < -self.sentiment_threshold:
                return "SELL"
            return "HOLD"
        except Exception as e:
            logger.error(f"Error generating sentiment signal: {str(e)}")
            return "HOLD"

class MomentumTrader(Trader):
    def __init__(self, db_handler: DatabaseHandler, lookback_period=5, volume_threshold=1.3):
        super().__init__(db_handler)
        self.lookback_period = lookback_period
        self.volume_threshold = volume_threshold

    def generate_signal(self, data: Dict[str, Any]) -> str:
        try:
            df = data['market_data']
            if df.empty:
                logger.info("No market data.")
                return "HOLD"

            df['returns'] = df['close_price'].pct_change()
            df['volume_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()

            recent = df.head(self.lookback_period)
            momentum = recent['returns'].mean()
            volume_signal = recent['volume_ratio'].mean() > self.volume_threshold

            logger.info(f"Momentum={momentum:.4f}, Volume OK={volume_signal}")

            if momentum > 0.01 and volume_signal:
                return "BUY"
            elif momentum < -0.01 and volume_signal:
                return "SELL"

            return "HOLD"
        except Exception as e:
            logger.error(f"Error generating momentum signal: {str(e)}")
            return "HOLD"

class MeanReversionTrader(Trader):
    def __init__(self, db_handler: DatabaseHandler, ma_period=20, deviation_threshold=0.03):
        super().__init__(db_handler)
        self.ma_period = ma_period
        self.deviation_threshold = deviation_threshold

    def generate_signal(self, data: Dict[str, Any]) -> str:
        try:
            df = data['market_data']
            if df.empty:
                logger.info("No market data.")
                return "HOLD"

            df['ma'] = df['close_price'].rolling(window=self.ma_period).mean()
            df['deviation'] = (df['close_price'] - df['ma']) / df['ma']

            latest_dev = df['deviation'].iloc[0]
            logger.info(f"Deviation from MA: {latest_dev:.4f}")

            if latest_dev < -self.deviation_threshold:
                return "BUY"
            elif latest_dev > self.deviation_threshold:
                return "SELL"

            return "HOLD"
        except Exception as e:
            logger.error(f"Error generating mean reversion signal: {str(e)}")
            return "HOLD"

class MultiFactorTrader(Trader):
    def __init__(self, db_handler: DatabaseHandler, technical_weight=0.4, fundamental_weight=0.3, sentiment_weight=0.3):
        super().__init__(db_handler)
        self.technical_weight = technical_weight
        self.fundamental_weight = fundamental_weight
        self.sentiment_weight = sentiment_weight

        self.momentum_trader = MomentumTrader(db_handler)
        self.mean_reversion_trader = MeanReversionTrader(db_handler)
        self.fundamental_trader = FundamentalTrader(db_handler)
        self.sentiment_trader = SentimentTrader(db_handler)

    def _signal_to_score(self, signal):
        if signal == "BUY": return 1
        if signal == "SELL": return -1
        return 0

    def generate_signal(self, data: Dict[str, Any]) -> str:
        try:
            m_signal = self.momentum_trader.generate_signal(data)
            r_signal = self.mean_reversion_trader.generate_signal(data)
            f_signal = self.fundamental_trader.generate_signal(data)
            s_signal = self.sentiment_trader.generate_signal(data)

            scores = {
                'momentum': self._signal_to_score(m_signal),
                'mean_rev': self._signal_to_score(r_signal),
                'fundamental': self._signal_to_score(f_signal),
                'sentiment': self._signal_to_score(s_signal)
            }

            technical_score = (scores['momentum'] + scores['mean_rev']) / 2
            final_score = (
                technical_score * self.technical_weight +
                scores['fundamental'] * self.fundamental_weight +
                scores['sentiment'] * self.sentiment_weight
            )

            logger.info(f"Scores - Momentum: {scores['momentum']}, MeanRev: {scores['mean_rev']}, "
                        f"Fundamental: {scores['fundamental']}, Sentiment: {scores['sentiment']}, "
                        f"Weighted: {final_score:.4f}")

            if final_score > 0.3:
                return "BUY"
            elif final_score < -0.3:
                return "SELL"
            return "HOLD"
        except Exception as e:
            logger.error(f"Error generating multifactor signal: {str(e)}")
            return "HOLD"
