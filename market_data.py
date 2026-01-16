import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

class MarketDataProvider:
    """
    Provides live market data for financial assets using yfinance.
    """
    def __init__(self):
        # yfinance can be used without any initial setup
        pass

    def get_current_price(self, ticker: str) -> float | None:
        """
        Fetches the most recent market price for a given ticker symbol.
        
        For silver, a common ticker is 'XAGUSD=X'.
        
        :param ticker: The ticker symbol (e.g., 'XAGUSD=X').
        :return: The current price as a float, or None if an error occurs.
        """
        try:
            stock = yf.Ticker(ticker)
            # Fetch data for the last day with a 1-minute interval to get recent price
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
            hist = stock.history(start=start_date, end=end_date, interval="1m")
            
            if not hist.empty:
                # The last available price in the fetched history
                last_price = hist['Close'].iloc[-1]
                return float(last_price)
            else:
                # Fallback for assets that may not have 1m data (e.g., after-hours)
                # 'fast_info' provides a recent price
                price = stock.fast_info.get('last_price')
                if price:
                    return float(price)
                print(f"Warning: Could not fetch price history for {ticker}. The ticker may be invalid or delisted.")
                return None

        except Exception as e:
            print(f"Error fetching price for {ticker} from yfinance: {e}")
            return None

    def get_historical_data(self, ticker: str, period: str = "1d", interval: str = "5m") -> pd.DataFrame | None:
        """
        Fetches historical market data for a given ticker.

        :param ticker: The ticker symbol (e.g., 'SI=F').
        :param period: The period to fetch data for (e.g., "1d", "5d", "1mo").
        :param interval: The data interval (e.g., "1m", "5m", "15m", "1h").
        :return: A pandas DataFrame with the historical data, or None.
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)

            if hist.empty:
                print(f"Warning: Could not fetch price history for {ticker}.")
                return None
            
            return hist

        except Exception as e:
            print(f"Error fetching historical data for {ticker} from yfinance: {e}")
            return None

    def get_technical_indicators(self, hist_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates technical indicators based on historical data.

        :param hist_df: DataFrame with historical data (must contain a 'Close' column).
        :return: DataFrame with added columns for indicators.
        """
        # Short-term and long-term moving averages
        hist_df['MA20'] = hist_df['Close'].rolling(window=20).mean()
        hist_df['MA50'] = hist_df['Close'].rolling(window=50).mean()

        # Relative Strength Index (RSI)
        delta = hist_df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist_df['RSI'] = 100 - (100 / (1 + rs))

        return hist_df


if __name__ == '__main__':
    # Example usage:
    provider = MarketDataProvider()
    silver_price = provider.get_current_price('SI=F')
    if silver_price:
        print(f"The current price of Silver (SI=F) is: ${silver_price:.2f}")
    else:
        print("Could not retrieve the price of Silver.")
    
    hist_data = provider.get_historical_data('SI=F')
    if hist_data:
        print(f"Fetched {len(hist_data)} historical data points.")
        print(f"Last data point: {datetime.fromtimestamp(hist_data[-1][0]/1000)} - ${hist_data[-1][1]:.2f}")
