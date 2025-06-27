import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
import logging
from typing import List, Optional

from data_layer.storage.db_handler import DatabaseHandler
from data_layer.storage.models import MarketData

logger = logging.getLogger(__name__)

class MarketDataCollector:
    def __init__(self, db_handler: DatabaseHandler):
        """
        Initializes the collector with a database handler.
        No API key is needed for yfinance.
        """
        self.db_handler = db_handler

    def fetch_market_data(self, tickers: List[str], interval: str,
                         start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch market data for a list of tickers using yfinance.
        This method is efficient as yfinance downloads all tickers in a single request.

        Args:
            tickers: A list of stock ticker symbols.
            interval: Data interval (e.g., '5m', '1h', '1d').
            start_date: The start date for the data.
            end_date: The end date for the data.

        Returns:
            A pandas DataFrame containing the formatted market data for all tickers.
        """
        logger.info(f"Fetching data for {tickers} from {start_date} to {end_date} with interval {interval}")
        try:
            # yfinance uses a specific format for intervals.
            # Note: yfinance has limitations on short intervals for long date ranges.
            # e.g., 1m data is only available for the last 7 days.
            data = yf.download(
                tickers=tickers,
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True,  # Handles stock splits and dividends
                progress=False,    # Disables the progress bar for cleaner logs
                group_by='ticker'  # Groups data by ticker for easier processing
            )

            if data.empty:
                logger.warning("No data returned from yfinance for the given parameters.")
                return pd.DataFrame()

            # Process the downloaded data into a clean, long-format DataFrame
            # that matches our database schema.
            all_data = []
            for ticker in tickers:
                if ticker in data and not data[ticker].empty:
                    ticker_df = data[ticker].copy()
                    ticker_df = ticker_df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
                    ticker_df['ticker'] = ticker
                    all_data.append(ticker_df)

            if not all_data:
                logger.warning("All ticker data was empty or NaN.")
                return pd.DataFrame()

            # Combine the list of DataFrames and reset the index to make 'timestamp' a column
            combined_df = pd.concat(all_data)
            combined_df.reset_index(inplace=True)
            # Rename columns to match the 'MarketData' model
            combined_df.rename(columns={
                'index': 'timestamp',
                'Open': 'open_price',
                'High': 'high_price',
                'Low': 'low_price',
                'Close': 'close_price',
                'Volume': 'volume'
            }, inplace=True)

            return combined_df

        except Exception as e:
            logger.error(f"An error occurred during yfinance data fetch: {e}", exc_info=True)
            return pd.DataFrame()

    def store_market_data(self, data: pd.DataFrame, interval: str):
        """
        Stores a DataFrame of market data into the database.

        Args:
            data: A DataFrame with market data.
            interval: The data interval (e.g., '5m').
        """
        session = self.db_handler.get_session()
        try:
            records_to_add = []
            for _, row in data.iterrows():
                # Ensure the timestamp from yfinance is timezone-aware (it's usually localized)
                ts = row['timestamp']
                if ts.tzinfo is None:
                    # If for some reason it's naive, assume UTC as a standard
                    ts = ts.tz_localize('UTC')
                else:
                    # Otherwise, convert it to UTC for consistent storage
                    ts = ts.astimezone(timezone.utc)

                record = MarketData(
                    ticker=row['ticker'],
                    timestamp=ts,
                    open_price=float(row['open_price']),
                    high_price=float(row['high_price']),
                    low_price=float(row['low_price']),
                    close_price=float(row['close_price']),
                    volume=int(row['volume']),
                    interval=interval
                )
                records_to_add.append(record)

            if records_to_add:
                session.bulk_save_objects(records_to_add) # Efficiently insert all records
                session.commit()
                logger.info(f"Successfully stored {len(records_to_add)} market data records.")

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to store market data: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def collect_and_store(self, tickers: List[str], interval: str, start_date: datetime, end_date: datetime):
        """
        Orchestrates the fetching and storing of market data.
        This is now much simpler as we don't need to loop or sleep.
        """
        logger.info(f"--- Starting yfinance collection for {tickers} ---")
        market_data_df = self.fetch_market_data(tickers, interval, start_date, end_date)

        if not market_data_df.empty:
            self.store_market_data(market_data_df, interval)
        else:
            logger.warning("No data was fetched, so nothing will be stored.")
        logger.info(f"--- Finished yfinance collection for {tickers} ---")