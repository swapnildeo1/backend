import pandas as pd
import pandas_ta as ta
import math
import datetime

class TradingEngine:
    def __init__(self):
        # Configuration for technical indicators
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.atr_period = 14

    def analyze_data(self, df: pd.DataFrame, timeframe: str, symbol: str):
        """
        Analyzes historical data to find breakout patterns.
        df requires: ['open', 'high', 'low', 'close', 'volume']
        """
        if len(df) < self.macd_slow + self.macd_signal:
            return None # Not enough data

        # Calculate Indicators
        df.ta.rsi(length=self.rsi_period, append=True)
        df.ta.macd(fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal, append=True)
        df.ta.atr(length=self.atr_period, append=True)
        df.ta.sma(length=20, append=True) # 20 SMA for volume breakout baseline
        
        # We need the most recent closed candle (index -1)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 1. Identify Trend & Momentum
        macd_line = latest[f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
        macd_signal_line = latest[f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
        rsi = latest[f'RSI_{self.rsi_period}']
        atr = latest[f'ATRr_{self.atr_period}']
        
        # 2. Volume Breakout Check
        # Current volume > 1.5x of previous volume
        is_volume_breakout = latest['volume'] > (prev['volume'] * 1.5)
        
        signal = None
        
        # Bullish Breakout Condition:
        # MACD cross up, RSI > 50 and < 70 (not overbought yet), Volume Spike
        if macd_line > macd_signal_line and rsi > 50 and is_volume_breakout and latest['close'] > latest['open']:
            signal = "bullish"
            
        # Bearish Breakout Condition:
        # MACD cross down, RSI < 50 and > 30 (not oversold yet), Volume Spike
        elif macd_line < macd_signal_line and rsi < 50 and is_volume_breakout and latest['close'] < latest['open']:
            signal = "bearish"

        if not signal:
            return None # No clear signal

        # 3. Calculate Risk Level based on ATR percentage of close price
        atr_pct = (atr / latest['close']) * 100
        risk_level = "Low"
        if atr_pct > 1.5:
            risk_level = "High"
        elif atr_pct > 0.8:
            risk_level = "Medium"

        # 4. Determine Strikes (Simplified logic for Mockup)
        # In a real app, you would fetch options chain and pick Delta ~0.5 (ATM) and Delta ~0.3 (OTM)
        spot_price = latest['close']
        step_size = 100 if "NIFTY" in symbol.upper() else 500 if "BANK" in symbol.upper() else 100
        
        atm_strike = round(spot_price / step_size) * step_size
        
        strikes = []
        if signal == "bullish":
            strikes = [f"{atm_strike} CE", f"{atm_strike + step_size} CE"]
            entry_price = atr * 1.2 # Arbitrary options pricing logic for mock
        else:
            strikes = [f"{atm_strike} PE", f"{atm_strike - step_size} PE"]
            entry_price = atr * 1.1

        # 5. Targets and Stop Loss based on ATR
        sl = entry_price - (atr * 0.5)
        t1 = entry_price + (atr * 0.8)
        t2 = entry_price + (atr * 1.5)
        t3 = entry_price + (atr * 2.5)
        
        # 6. Timeframe estimate
        target_time = "Intraday" if timeframe == "1H" else "1-3 Days"
        
        # 7. Expiry Calculation (Mock - Current Thursday)
        today = datetime.date.today()
        # Find next Thursday (Weekly Expiry for Nifty/BankNifty)
        days_ahead = 3 - today.weekday()
        if days_ahead <= 0: # Target day already happened this week
            days_ahead += 7
        next_expiry = today + datetime.timedelta(days_ahead)

        return {
            "asset": symbol,
            "direction": signal,
            "timeframe": f"{timeframe} BO",
            "strikes": " / ".join(strikes),
            "expiry": next_expiry.strftime("%d %b %Y"),
            "risk": risk_level,
            "entry": f"{round(entry_price * 0.95)} - {round(entry_price * 1.05)}",
            "sl": str(round(sl)),
            "targets": [
                {"label": "T1", "val": str(round(t1))},
                {"label": "T2", "val": str(round(t2))},
                {"label": "T3", "val": str(round(t3))}
            ],
            "targetTime": target_time
        }
