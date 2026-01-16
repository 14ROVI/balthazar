from collections import deque
from enum import Enum
from domain.post import Post
from market_data import MarketDataProvider
import pandas as pd


class Signal(Enum):
    """Represents a trading signal."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Strategy:
    """
    Decides the final trading action based on a history of signals,
    market data, and the bot's own past actions.
    """

    def __init__(self, market_provider: MarketDataProvider, max_history: int = 100):
        """
        Initializes the Strategy module.

        :param market_provider: An instance of MarketDataProvider to get live prices.
        :param max_history: The maximum number of recent signals and actions to store.
        """
        self.market_data = market_provider
        self.recent_signals = deque(maxlen=max_history)
        self.past_actions = deque(maxlen=max_history)

    def add_signal(self, signal: Signal, post: Post):
        """Adds a new signal from the AI engine to the history."""
        self.recent_signals.append({'signal': signal, 'post': post})

    def record_action(self, action: Signal):
        """Records a trading action taken by the bot."""
        self.past_actions.append(action)

    def decide(self) -> Signal:
        """
        Makes a trading decision (BUY, SELL, HOLD) based on AI signals
        and technical indicators.
        """
        if not self.recent_signals:
            return Signal.HOLD

        # 1. Get the latest AI signal
        latest_ai_signal = self.recent_signals[-1]['signal']

        # 2. Get historical data to calculate technical indicators
        # Fetching more data to ensure MA50 is calculated properly
        hist_df = self.market_data.get_historical_data(ticker='SI=F', period="10d", interval="5m")
        
        if hist_df is None or hist_df.empty:
            print("Strategy: Could not get historical data. Falling back to latest AI signal.")
            return latest_ai_signal

        # 3. Calculate technical indicators
        indicators_df = self.market_data.get_technical_indicators(hist_df)
        
        # Get the latest indicator values
        latest_indicators = indicators_df.iloc[-1]
        ma20 = latest_indicators.get('MA20')
        ma50 = latest_indicators.get('MA50')
        rsi = latest_indicators.get('RSI')

        if pd.isna(ma20) or pd.isna(ma50) or pd.isna(rsi):
            print("Strategy: Could not calculate all indicators. Falling back to latest AI signal.")
            return latest_ai_signal

        # 4. Define the trading strategy rules
        is_uptrend = ma20 > ma50
        is_downtrend = ma20 < ma50
        is_overbought = rsi > 70
        is_oversold = rsi < 30

        print(f"Strategy Insight: Trend is {'UP' if is_uptrend else 'DOWN'}. RSI is {rsi:.2f}.")

        # --- Decision Logic ---
        if latest_ai_signal == Signal.BUY:
            # BUY if AI says BUY, we're in an uptrend, and it's not overbought
            if is_uptrend and not is_overbought:
                print("DECISION: BUY (AI Signal + Uptrend + Not Overbought)")
                return Signal.BUY
            else:
                print("DECISION: HOLD (AI BUY signal did not meet trend/RSI criteria)")
                return Signal.HOLD

        elif latest_ai_signal == Signal.SELL:
            # SELL if AI says SELL, we're in a downtrend, and it's not oversold
            if is_downtrend and not is_oversold:
                print("DECISION: SELL (AI Signal + Downtrend + Not Oversold)")
                return Signal.SELL
            else:
                print("DECISION: HOLD (AI SELL signal did not meet trend/RSI criteria)")
                return Signal.HOLD

        # If AI signal is HOLD, we also hold.
        print("DECISION: HOLD (AI Signal was HOLD)")
        return Signal.HOLD
