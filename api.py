from fastapi import FastAPI
from starlette.responses import FileResponse
import os
import pandas as pd
from datetime import datetime, timedelta, timezone

from db import Database
from market_data import MarketDataProvider

# --- Initialization ---
app = FastAPI()
db = Database()
market_provider = MarketDataProvider()

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.join(current_dir, "dashboard")


# --- Static File Serving ---

@app.get("/")
async def get_index():
    """Serves the main index.html dashboard file."""
    html_path = os.path.join(dashboard_dir, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"error": "index.html not found"}


# --- API Endpoints ---

@app.get("/api/price-history")
async def get_price_history():
    """
    Provides historical price data for the silver futures ticker,
    updated every minute.
    """
    hist_df = market_provider.get_historical_data(ticker='SI=F', period="1d", interval="1m")
    
    if hist_df is not None and not hist_df.empty:
        # Reset index to make 'Datetime' a column
        hist_df = hist_df.reset_index()
        
        # Convert timezone-aware Datetime to UTC timestamp in milliseconds for JS
        hist_df['timestamp'] = hist_df['Datetime'].apply(lambda x: int(x.timestamp() * 1000))
        
        # Select and format the data
        chart_data = hist_df[['timestamp', 'Close']].values.tolist()
        return {"prices": chart_data}
        
    return {"error": "Could not fetch price history"}

@app.get("/api/sentiment")
async def get_sentiment():
    """
    Calculates and provides aggregated sentiment data based on signals
    from the last 24 hours.
    """
    # 1. Fetch signals from the last 24 hours
    twenty_four_hours_ago = int((datetime.now() - timedelta(hours=24)).timestamp())
    signals = db.get_signals_since(twenty_four_hours_ago)

    if not signals:
        return {
            "pie_chart": {"buy": 0, "sell": 0, "hold": 0},
            "volume_chart": [],
        }

    # 2. Use pandas to process the data
    df = pd.DataFrame([s.__dict__ for s in signals])
    df['timestamp'] = pd.to_datetime(df['added'], unit='s', utc=True)
    df.set_index('timestamp', inplace=True)

    # 3. Data for the Pie Chart (last 1 hour)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    last_hour_df = df[df.index >= one_hour_ago]
    pie_chart_data = last_hour_df['signal'].value_counts().to_dict()
    # Ensure all keys exist
    pie_chart_data.setdefault('BUY', 0)
    pie_chart_data.setdefault('SELL', 0)
    pie_chart_data.setdefault('HOLD', 0)
    
    # Convert numpy types to native Python types for JSON serialization
    for key, value in pie_chart_data.items():
        pie_chart_data[key] = int(value)

    # 4. Data for the Buy/Sell Volume Chart
    # Create separate columns for buy and sell counts
    df['buy'] = (df['signal'] == 'BUY').astype(int)
    df['sell'] = (df['signal'] == 'SELL').astype(int)
    df['hold'] = (df['signal'] == 'HOLD').astype(int)

    # Resample into 15-minute intervals, summing the counts
    sentiment_volume = df[['buy', 'sell']].resample('15min').sum()

    # Format for ApexCharts
    volume_chart_data = [
        {'x': int(index.timestamp() * 1000), 'y_buy': int(row['buy']), 'y_sell': int(row['sell'])}
        for index, row in sentiment_volume.iterrows()
    ]

    # 5. Data for Rolling Sentiment Percentage Chart
    # Resample to 15min to have a consistent time basis
    resampled_df = df[['buy', 'sell', 'hold']].resample('15min').sum()
    
    # Calculate a rolling sum with a 1-hour window (4 * 15-minute periods)
    rolling_sentiment = resampled_df.rolling(window=4).sum()

    # Calculate the total number of signals in each rolling window
    rolling_sentiment['total'] = rolling_sentiment['buy'] + rolling_sentiment['sell'] + rolling_sentiment['hold']

    # Calculate the percentage of each sentiment
    # Avoid division by zero
    rolling_sentiment['buy_pct'] = (rolling_sentiment['buy'] / rolling_sentiment['total']).fillna(0) * 100
    rolling_sentiment['sell_pct'] = (rolling_sentiment['sell'] / rolling_sentiment['total']).fillna(0) * 100
    rolling_sentiment['hold_pct'] = (rolling_sentiment['hold'] / rolling_sentiment['total']).fillna(0) * 100

    # Format for ApexCharts
    rolling_chart_data = [
        {
            'x': int(index.timestamp() * 1000),
            'y_buy': row['buy_pct'],
            'y_sell': row['sell_pct'],
            'y_hold': row['hold_pct']
        }
        for index, row in rolling_sentiment.iterrows()
    ]
    
    return {
        "pie_chart": pie_chart_data,
        "volume_chart": volume_chart_data,
        "rolling_sentiment": rolling_chart_data,
    }



