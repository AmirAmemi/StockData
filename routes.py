# routes.py
from fastapi import APIRouter, HTTPException, Depends, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uuid
import logging
from datetime import datetime, timedelta
import asyncio

from models import (
    StockData, CryptoData, AlternativeDataBatch, 
    MarketSentiment, DataQuery, APIResponse,
    DataSourceType, TimeFrame
)
from data_processor import (
    fetch_market_data, fetch_crypto_data, 
    fetch_sentiment_data, process_alternative_data,
    get_streaming_data
)
from config import get_settings, Settings

logger = logging.getLogger("bavest-api")
router = APIRouter()

@router.post("/market/data", response_model=APIResponse, tags=["Market Data"])
async def get_market_data(query: DataQuery, settings: Settings = Depends(get_settings)):
    """
    Fetch market data based on provided query parameters
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Request {request_id}: Market data request for {query.symbols}")
    
    try:
        if query.data_source == DataSourceType.MARKET:
            data = await fetch_market_data(
                symbols=query.symbols,
                start_date=query.start_date,
                end_date=query.end_date or datetime.utcnow(),
                timeframe=query.timeframe,
                limit=query.limit
            )
        elif query.data_source == DataSourceType.BLOCKCHAIN:
            data = await fetch_crypto_data(
                symbols=query.symbols,
                start_date=query.start_date,
                end_date=query.end_date or datetime.utcnow(),
                timeframe=query.timeframe,
                limit=query.limit
            )
        else:
            raise HTTPException(status_code=400, detail=f"Data source {query.data_source} not supported for this endpoint")
            
        return APIResponse(
            success=True,
            message=f"Successfully fetched {len(data)} data points",
            data=data,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Request {request_id}: Error fetching market data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/stocks/{symbol}", response_model=APIResponse, tags=["Market Data"])
async def get_stock_data(
    symbol: str = Path(..., description="Stock ticker symbol"),
    days: int = Query(30, description="Number of days of historical data"),
    timeframe: TimeFrame = Query(TimeFrame.ONE_DAY, description="Data timeframe")
):
    """
    Get historical stock data for a specific symbol
    """
    request_id = str(uuid.uuid4())
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        data = await fetch_market_data(
            symbols=[symbol.upper()],
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe
        )
        
        return APIResponse(
            success=True,
            message=f"Successfully fetched stock data for {symbol}",
            data=data,
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Request {request_id}: Error fetching stock data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching stock data: {str(e)}")

@router.get("/crypto/{symbol}", response_model=APIResponse, tags=["Market Data"])
async def get_crypto_data(
    symbol: str = Path(..., description="Cryptocurrency symbol (e.g., BTCUSDT)"),
    days: int = Query(30, description="Number of days of historical data"),
    timeframe: TimeFrame = Query(TimeFrame.ONE_HOUR, description="Data timeframe")
):
    """
    Get historical cryptocurrency data for a specific symbol
    """
    request_id = str(uuid.uuid4())
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        data = await fetch_crypto_data(
            symbols=[symbol.upper()],
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe
        )
        
        return APIResponse(
            success=True,
            message=f"Successfully fetched crypto data for {symbol}",
            data=data,
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Request {request_id}: Error fetching crypto data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching crypto data: {str(e)}")

@router.get("/sentiment/{symbol}", response_model=APIResponse, tags=["Alternative Data"])
async def get_sentiment_data(
    symbol: str = Path(..., description="Asset symbol"),
    days: int = Query(7, description="Number of days of sentiment data"),
    sources: Optional[List[str]] = Query(None, description="Specific sources to include")
):
    """
    Get sentiment data for a specific asset symbol
    """
    request_id = str(uuid.uuid4())
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        data = await fetch_sentiment_data(
            symbol=symbol.upper(),
            start_date=start_date,
            end_date=end_date,
            sources=sources
        )
        
        return APIResponse(
            success=True,
            message=f"Successfully fetched sentiment data for {symbol}",
            data=data,
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"Request {request_id}: Error fetching sentiment data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching sentiment data: {str(e)}")

@router.post("/alternative/process", response_model=APIResponse, tags=["Alternative Data"])
async def process_data(
    data: AlternativeDataBatch,
    background_tasks: BackgroundTasks
):
    """
    Process a batch of alternative data and return insights
    """
    request_id = str(uuid.uuid4())
    try:
        # Process data asynchronously in background
        background_tasks.add_task(
            process_alternative_data,
            data=data,
            request_id=request_id
        )
        
        return APIResponse(
            success=True,
            message=f"Data processing started for {data.data_type} from {data.source}",
            request_id=request_id,
            data={"status": "processing", "points_received": len(data.data_points)}
        )
    except Exception as e:
        logger.error(f"Request {request_id}: Error processing alternative data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@router.websocket("/stream/{symbol}")
async def websocket_endpoint(websocket, symbol: str):
    """
    Stream real-time data for a specific symbol
    """
    await websocket.accept()
    
    try:
        async for data_point in get_streaming_data(symbol):
            if data_point:
                await websocket.send_json(data_point)
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Streaming error for {symbol}: {str(e)}")
        await websocket.close(code=1000)