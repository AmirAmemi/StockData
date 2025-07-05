# models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Any
from datetime import datetime
from enum import Enum

class DataSourceType(str, Enum):
    MARKET = "market"
    ALTERNATIVE = "alternative"
    SOCIAL = "social"
    NEWS = "news"
    BLOCKCHAIN = "blockchain"

class TimeFrame(str, Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"

class StockData(BaseModel):
    """Model for stock/equity data"""
    symbol: str
    exchange: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": [
                {
                "symbol": "AAPL",
                "exchange": "NASDAQ",
                "timestamp": "2023-07-10T16:00:00Z",
                "open": 188.94,
                "high": 189.97,
                "low": 187.04,
                "close": 188.61,
                "volume": 45587600,
                "adjusted_close": 188.61
                }
            ]
        }

class CryptoData(BaseModel):
    """Model for cryptocurrency data"""
    symbol: str
    base_asset: str
    quote_asset: str
    exchange: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trades: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": [
                {
                "symbol": "BTCUSDT",
                "base_asset": "BTC",
                "quote_asset": "USDT",
                "exchange": "Binance",
                "timestamp": "2023-07-10T16:00:00Z",
                "open": 30241.50,
                "high": 30298.75,
                "low": 29975.12,
                "close": 30150.25,
                "volume": 1243.85,
                "trades": 35762
                }
            ]
        }

class AlternativeDataPoint(BaseModel):
    """Model for a single alternative data point"""
    data_type: str
    source: str
    timestamp: datetime
    value: Union[float, str, int, bool, Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None

class AlternativeDataBatch(BaseModel):
    """Model for a batch of alternative data"""
    data_type: str
    source: str
    data_points: List[AlternativeDataPoint]
    
class MarketSentiment(BaseModel):
    """Model for market sentiment data"""
    symbol: str
    timestamp: datetime
    source: str
    sentiment_score: float  # -1.0 to 1.0
    volume: Optional[int] = None
    momentum_indicator: Optional[float] = None
    
class DataQuery(BaseModel):
    """Model for querying financial data"""
    symbols: List[str]
    data_source: DataSourceType
    start_date: datetime
    end_date: Optional[datetime] = None
    timeframe: TimeFrame = TimeFrame.ONE_DAY
    limit: Optional[int] = 1000
    
    class Config:
        json_schema_extra = {
            "example": [
                {
                "symbols": ["AAPL", "MSFT", "GOOGL"],
                "data_source": "market",
                "start_date": "2023-06-01T00:00:00Z",
                "end_date": "2023-07-01T00:00:00Z",
                "timeframe": "1d",
                "limit": 100
                }
            ]
        }

class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str