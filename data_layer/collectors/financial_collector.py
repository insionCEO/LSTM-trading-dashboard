import os
import time
import requests
import logging
from datetime import datetime
from data_layer.storage.db_handler import DatabaseHandler
from data_layer.storage.models import FinancialMetrics

logger = logging.getLogger(__name__)

class FinancialDataCollector:
    def __init__(self, db_handler: DatabaseHandler):
        self.db = db_handler
        self.api_key = os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable not set")
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

    def _make_request(self, endpoint: str, tickers: list):
        """Helper function to make and handle API requests gracefully."""
        joined_tickers = ",".join(tickers)
        url = f"{self.base_url}/{endpoint}?symbol={joined_tickers}&apikey={self.api_key}"
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Gracefully handle both explicit API errors and empty list responses
            if not data or (isinstance(data, dict) and data.get('Error Message')):
                if isinstance(data, dict):
                    logger.warning(f"FMP API returned an error for '{endpoint}': {data['Error Message']}")
                else:
                    logger.warning(f"FMP API returned no data for endpoint '{endpoint}'. This may be a plan limitation.")
                return {}
            
            # Return data indexed by symbol for easy lookup
            return {d["symbol"]: d for d in data}
        except requests.exceptions.RequestException as e:
            logger.error(f"Network request to FMP endpoint '{endpoint}' failed: {e}")
            return {}
        except Exception as e:
            logger.error(f"An unexpected error occurred processing FMP data for '{endpoint}': {e}")
            return {}

    def collect(self, tickers=None, start_date=None, end_date=None):
        tickers = tickers or self.symbols

        logger.info(f"Starting financial metrics collection for: {tickers}")
        ratios = self._make_request("ratios-ttm", tickers)
        profiles = self._make_request("profile", tickers)
        income_statements = self._make_request("income-statement-ttm", tickers)

        for symbol in tickers:
            try:
                r = ratios.get(symbol, {})
                p = profiles.get(symbol, {})
                i = income_statements.get(symbol, {})

                if not any([r, p, i]):
                    logger.warning(f"No financial data could be retrieved for {symbol}. Skipping database insert.")
                    continue

                # Create the object with any data we managed to get
                financials = FinancialMetrics(
                    ticker=symbol,
                    timestamp=datetime.utcnow(),
                    revenue=i.get("revenue"),
                    net_income=i.get("netIncome"),
                    eps=i.get("eps"),
                    market_cap=p.get("mktCap"),
                    pe_ratio=r.get("peRatioTTM"),
                    forward_pe=r.get("forwardPETTM"),
                    pb_ratio=r.get("priceToBookRatioTTM"),
                    peg_ratio=r.get("pegRatioTTM"),
                    profit_margin=r.get("netProfitMarginTTM"),
                    operating_margin=r.get("operatingMarginTTM"),
                    return_on_equity=r.get("returnOnEquityTTM"),
                    return_on_assets=r.get("returnOnAssetsTTM"),
                    current_ratio=r.get("currentRatioTTM"),
                    quick_ratio=r.get("quickRatioTTM"),
                    debt_to_equity=r.get("debtEquityRatioTTM")
                )

                self.db.insert(financials)
                logger.info(f"Successfully inserted available financial metrics for {symbol}")

            except Exception as e:
                logger.error(f"Failed to process and insert financial metrics for {symbol}: {e}")
            finally:
                time.sleep(0.5) # A small delay to be respectful to the API