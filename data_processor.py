# data_processor.py
import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, AsyncGenerator

import pandas as pd
import numpy as np
from scipy.stats import norm

from models import (
    StockData, CryptoData, MarketSentiment,
    AlternativeDataBatch, TimeFrame
)

logger = logging.getLogger("bavest-api")

# Mock data constants for demonstration
STOCK_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"]
CRYPTO_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]
SENTIMENT_SOURCES = ["twitter", "reddit", "news", "analyst_ratings", "forum_discussions"]

# Cached data storage
_market_data_cache = {}
_crypto_data_cache = {}
_sentiment_data_cache = {}

async def fetch_market_data(
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
    timeframe: TimeFrame = TimeFrame.ONE_DAY,
    limit: int = 1000
) -> List[StockData]:
    """
    Fetch market data for specified symbols and time range
    
    In a real implementation, this would connect to data providers, APIs, or databases.
    Here we generate mock data for demonstration purposes.
    """
    logger.info(f"Fetching market data for {symbols} from {start_date} to {end_date}")
    
    cache_key = f"{'-'.join(symbols)}_{start_date.isoformat()}_{end_date.isoformat()}_{timeframe}"
    if cache_key in _market_data_cache:
        logger.info(f"Returning cached market data for {cache_key}")
        return _market_data_cache[cache_key]
    
    # Simulation of API latency
    await asyncio.sleep(0.5)
    
    results = []
    for symbol in symbols:
        if symbol not in STOCK_SYMBOLS:
            # For demo, we'll generate data for unknown symbols too
            logger.warning(f"Symbol {symbol} not found in known stocks, generating mock data")
        
        # Generate time points based on timeframe
        time_delta = _get_timedelta_from_timeframe(timeframe)
        current_time = start_date
        
        # Base price for the asset (random but deterministic for the same symbol)
        base_price = sum(ord(c) for c in symbol) % 100 + 50
        
        # Generate price series with random walk and some volatility
        price_series = _generate_price_series(
            symbol, 
            base_price, 
            start_date, 
            end_date, 
            time_delta,
            limit
        )
        
        # Create StockData objects for each time point
        for timestamp, price_data in price_series.items():
            stock_data = StockData(
                symbol=symbol,
                exchange="NASDAQ",  # Mock exchange
                timestamp=timestamp,
                open=price_data["open"],
                high=price_data["high"],
                low=price_data["low"],
                close=price_data["close"],
                volume=price_data["volume"],
                adjusted_close=price_data["close"]
            )
            results.append(stock_data)
    
    # Cache the results
    _market_data_cache[cache_key] = results
    return results

async def fetch_crypto_data(
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
    timeframe: TimeFrame = TimeFrame.ONE_HOUR,
    limit: int = 1000
) -> List[CryptoData]:
    """
    Fetch cryptocurrency data for specified symbols and time range
    """
    logger.info(f"Fetching crypto data for {symbols} from {start_date} to {end_date}")
    
    cache_key = f"{'-'.join(symbols)}_{start_date.isoformat()}_{end_date.isoformat()}_{timeframe}"
    if cache_key in _crypto_data_cache:
        logger.info(f"Returning cached crypto data for {cache_key}")
        return _crypto_data_cache[cache_key]
    
    # Simulation of API latency
    await asyncio.sleep(0.5)
    
    results = []
    for symbol in symbols:
        # Parse base and quote assets from symbol (typically BTCUSDT format)
        if len(symbol) > 3:
            base_asset = symbol[:-4] if symbol.endswith("USDT") else symbol[:3]
            quote_asset = "USDT" if symbol.endswith("USDT") else symbol[3:]
        else:
            base_asset = symbol
            quote_asset = "USD"
        
        # Generate time points based on timeframe
        time_delta = _get_timedelta_from_timeframe(timeframe)
        
        # Base price for the crypto (random but deterministic for the same symbol)
        base_price = sum(ord(c) for c in symbol) % 1000 + 100
        if "BTC" in symbol:
            base_price *= 30  # Make BTC much higher
        elif "ETH" in symbol:
            base_price *= 3   # Make ETH somewhat higher
        
        # Generate price series with higher volatility than stocks
        price_series = _generate_price_series(
            symbol, 
            base_price, 
            start_date, 
            end_date, 
            time_delta,
            limit,
            volatility_factor=1.5  # Higher volatility for crypto
        )
        
        # Create CryptoData objects for each time point
        for timestamp, price_data in price_series.items():
            crypto_data = CryptoData(
                symbol=symbol,
                base_asset=base_asset,
                quote_asset=quote_asset,
                exchange="Binance",  # Mock exchange
                timestamp=timestamp,
                open=price_data["open"],
                high=price_data["high"],
                low=price_data["low"],
                close=price_data["close"],
                volume=price_data["volume"] / 10,  # Different volume scale for crypto
                trades=int(price_data["volume"] / 100)
            )
            results.append(crypto_data)
    
    # Cache the results
    _crypto_data_cache[cache_key] = results
    return results

async def fetch_sentiment_data(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    sources: Optional[List[str]] = None
) -> List[MarketSentiment]:
    """
    Fetch sentiment data for a specific asset symbol
    """
    logger.info(f"Fetching sentiment data for {symbol} from {start_date} to {end_date}")
    
    cache_key = f"{symbol}_{start_date.isoformat()}_{end_date.isoformat()}"
    if cache_key in _sentiment_data_cache:
        logger.info(f"Returning cached sentiment data for {cache_key}")
        return _sentiment_data_cache[cache_key]
    
    # Simulation of API latency
    await asyncio.sleep(0.3)
    
    # Use specified sources or default to all sources
    data_sources = sources if sources else SENTIMENT_SOURCES
    
    results = []
    # Generate daily sentiment scores
    current_date = start_date
    
    # Seed random based on symbol for consistent results
    random.seed(sum(ord(c) for c in symbol))
    
    while current_date <= end_date:
        for source in data_sources:
            # Generate a sentiment score between -1 and 1
            # with some natural time correlation (trending)
            day_factor = (current_date - start_date).days / max(1, (end_date - start_date).days)
            
            # Create a trend with some randomization
            base_sentiment = 0.2 * np.sin(day_factor * 6) + random.uniform(-0.3, 0.3)
            sentiment_score = max(-1.0, min(1.0, base_sentiment))
            
            # Volume of mentions/data points that contributed to the sentiment
            volume = int(random.uniform(100, 10000))
            
            sentiment_data = MarketSentiment(
                symbol=symbol,
                timestamp=current_date,
                source=source,
                sentiment_score=sentiment_score,
                volume=volume,
                momentum_indicator=sentiment_score * (1 + day_factor)
            )
            results.append(sentiment_data)
        
        current_date += timedelta(days=1)
    
    # Cache the results
    _sentiment_data_cache[cache_key] = results
    return results

async def process_alternative_data(data: AlternativeDataBatch, request_id: str) -> Dict[str, Any]:
    """
    Process alternative data and extract insights
    This would typically be a background task
    """
    logger.info(f"Processing {len(data.data_points)} alternative data points from {data.source}")
    
    # Simulate processing delay
    await asyncio.sleep(2)
    
    # In a real implementation, this would perform data analysis, ML predictions, etc.
    # For demonstration, we'll return some mock insights
    
    # Extract data values
    values = []
    for point in data.data_points:
        if isinstance(point.value, (int, float)):
            values.append(point.value)
        elif isinstance(point.value, dict) and 'value' in point.value:
            if isinstance(point.value['value'], (int, float)):
                values.append(point.value['value'])
    
    # Generate mock insights if we have numeric values
    insights = {}
    if values:
        values_array = np.array(values)
        insights = {
            "count": len(values),
            "mean": float(np.mean(values_array)),
            "median": float(np.median(values_array)),
            "std_dev": float(np.std(values_array)),
            "min": float(np.min(values_array)),
            "max": float(np.max(values_array)),
            "processed_at": datetime.utcnow().isoformat()
        }
    
    # Log processing completion
    logger.info(f"Request {request_id}: Finished processing alternative data")
    
    return insights

async def get_streaming_data(symbol: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate streaming data for a given symbol
    In a real implementation, this would connect to a market data stream
    """
    logger.info(f"Starting data stream for {symbol}")
    
    # Generate initial price based on symbol
    base_price = sum(ord(c) for c in symbol) % 100 + 50
    current_price = base_price
    
    # Stream data indefinitely (until client disconnects)
    try:
        while True:
            # Update price with random walk
            price_change = random.uniform(-1, 1) * (current_price * 0.005)  # 0.5% volatility
            current_price += price_change
            
            # Create data point
            timestamp = datetime.utcnow()
            data_point = {
                "symbol": symbol,
                "timestamp": timestamp.isoformat(),
                "price": current_price,
                "volume": random.randint(100, 10000),
                "trade_count": random.randint(10, 200)
            }
            
            yield data_point
            await asyncio.sleep(1)  # Stream data every second
    except Exception as e:
        logger.error(f"Error in data stream for {symbol}: {str(e)}")
    finally:
        logger.info(f"Closing data stream for {symbol}")

# Helper functions
def _get_timedelta_from_timeframe(timeframe: TimeFrame) -> timedelta:
    """Convert TimeFrame enum to timedelta object"""
    mapping = {
        TimeFrame.ONE_MINUTE: timedelta(minutes=1),
        TimeFrame.FIVE_MINUTES: timedelta(minutes=5),
        TimeFrame.FIFTEEN_MINUTES: timedelta(minutes=15),
        TimeFrame.THIRTY_MINUTES: timedelta(minutes=30),
        TimeFrame.ONE_HOUR: timedelta(hours=1),
        TimeFrame.FOUR_HOURS: timedelta(hours=4),
        TimeFrame.ONE_DAY: timedelta(days=1),
        TimeFrame.ONE_WEEK: timedelta(weeks=1),
        TimeFrame.ONE_MONTH: timedelta(days=30)
    }
    return mapping.get(timeframe, timedelta(days=1))

def _generate_price_series(
    symbol: str,
    base_price: float,
    start_date: datetime,
    end_date: datetime,
    time_delta: timedelta,
    limit: int = 1000,
    volatility_factor: float = 1.0
) -> Dict[datetime, Dict[str, float]]:
    """
    Generate a series of price data points using geometric Brownian motion
    """
    # Seed random based on symbol for consistent results
    random.seed(sum(ord(c) for c in symbol))
    np.random.seed(sum(ord(c) for c in symbol))
    
    # Parameters for the geometric Brownian motion
    mu = 0.0001 * time_delta.total_seconds() / 86400  # Expected return (annualized)
    sigma = 0.01 * volatility_factor * np.sqrt(time_delta.total_seconds() / 86400)  # Volatility
    
    # Generate time points
    time_points = []
    current_time = start_date
    while current_time <= end_date and len(time_points) < limit:
        time_points.append(current_time)
        current_time += time_delta
    
    # Limit to the requested number of points
    time_points = time_points[:limit]
    
    # Generate price path
    price_path = [base_price]
    for i in range(1, len(time_points)):
        # Generate daily returns using GBM
        random_return = np.random.normal(mu, sigma)
        new_price = price_path[-1] * np.exp(random_return)
        price_path.append(new_price)
    
    # Create the price series with OHLC data
    price_series = {}
    for i, timestamp in enumerate(time_points):
        close_price = price_path[i]
        
        # Generate open, high, low based on close price
        daily_volatility = sigma * close_price
        open_price = close_price * (1 + random.uniform(-0.5, 0.5) * daily_volatility)
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 1) * daily_volatility)
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 1) * daily_volatility)
        
        # Generate volume
        volume_base = int(close_price * 1000)
        volume = int(volume_base * (1 + random.uniform(-0.5, 1.5)))
        
        price_series[timestamp] = {
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume
        }
    
    return price_series