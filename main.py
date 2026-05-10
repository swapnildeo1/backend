from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
import uvicorn
import pandas as pd
import random
from engine import TradingEngine

app = FastAPI(title="QuantumTrade Alert Backend")
engine = TradingEngine()

# Mock Database
class Settings(BaseModel):
    mobile_number: str
    gateway: str
    indices: List[str]

current_settings = Settings(
    mobile_number="9876543210",
    gateway="whatsapp",
    indices=["NIFTY", "BANKNIFTY"]
)

# Mock Data Generator
def generate_mock_ohlcv():
    # Generates a DataFrame with random but somewhat realistic price action for testing
    data = []
    base_price = 22000
    for i in range(50):
        open_price = base_price + random.uniform(-20, 20)
        high_price = open_price + random.uniform(0, 50)
        low_price = open_price - random.uniform(0, 50)
        close_price = open_price + random.uniform(-40, 40)
        volume = random.randint(10000, 50000)
        # Force a breakout on the last candle randomly
        if i == 49:
            close_price = open_price + random.uniform(50, 100) # Bullish breakout
            volume = random.randint(80000, 150000) # Volume spike
        data.append([open_price, high_price, low_price, close_price, volume])
        base_price = close_price
        
    return pd.DataFrame(data, columns=['open', 'high', 'low', 'close', 'volume'])

def send_alert_via_gateway(alert_data: dict, phone: str, gateway: str):
    """
    Mock function to simulate sending SMS/WhatsApp via Fast2SMS / Twilio
    """
    message = f"""🚨 BREAKOUT ALERT 🚨
Index: {alert_data['asset']} ({alert_data['direction'].capitalize()} Momentum)
Risk Level: {alert_data['risk']} (Volatile Market)
Timeframe to Target: {alert_data['targetTime']}

Buy: {alert_data['strikes']}
Entry Price: {alert_data['entry']}
Stop Loss: {alert_data['sl']}
Targets: T1: {alert_data['targets'][0]['val']}, T2: {alert_data['targets'][1]['val']}, T3: {alert_data['targets'][2]['val']}
"""
    print(f"\n--- DISPATCHING ALERT VIA {gateway.upper()} TO {phone} ---")
    print(message)
    print("---------------------------------------------------\n")

@app.get("/api/alerts")
def get_live_alerts():
    """
    Endpoint to trigger analysis and return active alerts
    """
    alerts = []
    for symbol in current_settings.indices:
        # 1. Fetch mock data (In real app, fetch from Dhan/Angel One API)
        df = generate_mock_ohlcv()
        
        # 2. Run Analysis
        result = engine.analyze_data(df, timeframe="1H", symbol=symbol)
        
        if result:
            result['id'] = random.randint(1000, 9999)
            result['timestamp'] = datetime.datetime.now().isoformat()
            alerts.append(result)
            
            # Dispatch async alert
            send_alert_via_gateway(result, current_settings.mobile_number, current_settings.gateway)
            
    return {"status": "success", "alerts": alerts}

@app.post("/api/settings")
def update_settings(settings: Settings):
    global current_settings
    current_settings = settings
    return {"status": "success", "message": "Settings updated"}

@app.get("/api/settings")
def get_settings():
    return current_settings

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
