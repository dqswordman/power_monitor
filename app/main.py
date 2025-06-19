from typing import List, Dict, Optional
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from datetime import datetime, timedelta

from . import config
from .pma_client import fetch_latest, fetch_by_time_range
from .models import DataRecord

DESC = """
MUT Power Monitor · Demo API

* `/latest`             — 最近 N 行原始数据  
* `/summary`            — 最近 N 行楼栋有功功率汇总
* `/hourly/latest`      — 最近一小时的全部原始数据
* `/hourly/summary`     — 最近一小时楼栋有功功率汇总
* `/daily/latest`       — 最近一天的全部原始数据
* `/daily/summary`      — 最近一天楼栋有功功率汇总
* `/weekly/latest`      — 最近一周的全部原始数据
* `/weekly/summary`     — 最近一周楼栋有功功率汇总
* `/monthly/latest`     — 最近一个月的全部原始数据
* `/monthly/summary`    — 最近一个月楼栋有功功率汇总
* `/custom/latest`      — 自定义时间范围的全部原始数据（最长7天）
* `/custom/summary`     — 自定义时间范围的楼栋有功功率汇总（最长7天）
"""

app = FastAPI(
    title="MUT Power Monitor API",
    version="0.3.0",
    description=DESC,
)


def _to_float_safe(value: str) -> float:
    """处理空字符串/异常值"""
    try:
        return float(value)
    except ValueError:
        return 0.0


def _aggregate_by_building(rows: List[Dict]) -> Dict[str, float]:
    """
    返回 {Building: total_kW}（三相 power 之和）
    """
    agg: Dict[str, float] = {}
    for row in rows:
        bld = row.get("Building") or "UNKNOWN"
        total_kw = (
            _to_float_safe(row.get("power1", 0)) +
            _to_float_safe(row.get("power2", 0)) +
            _to_float_safe(row.get("power3", 0))
        )
        agg[bld] = agg.get(bld, 0.0) + total_kw
    return agg


def _process_raw_data(rows: List[Dict]) -> List[Dict]:
    """处理原始数据，确保格式正确"""
    processed_rows = []
    for row in rows:
        processed_row = {
            "id": row.get("id", 0),
            "timestamp1": row.get("timestamp1", ""),  # 使用数据库字段名
            "volt1": row.get("volt1", 0),
            "volt2": row.get("volt2", 0),
            "volt3": row.get("volt3", 0),
            "current1": row.get("current1", 0),
            "current2": row.get("current2", 0),
            "current3": row.get("current3", 0),
            "power1": row.get("power1", 0),
            "power2": row.get("power2", 0),
            "power3": row.get("power3", 0),
            "energy1": row.get("energy1", 0),
            "energy2": row.get("energy2", 0),
            "energy3": row.get("energy3", 0),
            "Building": row.get("Building", "UNKNOWN"),
            "Floor": row.get("Floor")
        }
        processed_rows.append(processed_row)
    return processed_rows


async def _validate_date_range(start_date: str, end_date: str):
    """验证日期范围是否有效且不超过7天"""
    try:
        # 尝试解析日期，支持多种格式
        # 如果只有日期部分（没有时间），自动添加时间
        if "T" not in start_date and " " not in start_date and len(start_date.split("-")) == 3:
            start_dt = datetime.fromisoformat(f"{start_date}T00:00:00")
        else:
            start_dt = datetime.fromisoformat(start_date)
            
        if "T" not in end_date and " " not in end_date and len(end_date.split("-")) == 3:
            # 对于结束日期，如果只提供日期，设置为当天结束时间
            end_dt = datetime.fromisoformat(f"{end_date}T23:59:59")
        else:
            end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="日期格式无效，请使用ISO格式：YYYY-MM-DD 或 YYYY-MM-DDThh:mm:ss 或 YYYY-MM-DD hh:mm:ss"
        )
    
    if end_dt < start_dt:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")
    
    delta = end_dt - start_dt
    if delta.days > 7:
        raise HTTPException(status_code=400, detail="时间范围不能超过7天")
    
    return start_dt, end_dt


@app.get("/latest", response_model=List[DataRecord])
async def latest(
    n: int = Query(
        config.DEFAULT_LIMIT,
        ge=1,
        le=config.MAX_LIMIT,
        description="返回行数 (1-100)"
    )
):
    """最近 N 行记录"""
    try:
        rows = await run_in_threadpool(fetch_latest, n)
        
        # 调试：打印第一行数据的字段
        if rows:
            print(f"Debug - First row keys: {list(rows[0].keys())}")
            print(f"Debug - First row: {rows[0]}")
        
        # 确保数据格式正确
        processed_rows = _process_raw_data(rows)
        
        return processed_rows
    except Exception as e:
        print(f"Error in latest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summary")
async def summary(
    n: int = Query(
        config.DEFAULT_LIMIT,
        ge=1,
        le=config.MAX_LIMIT,
        description="汇总最近 N 行"
    )
):
    """最近 N 行 → 按楼栋统计累计有功功率(kW)。"""
    try:
        rows = await run_in_threadpool(fetch_latest, n)
        agg = _aggregate_by_building(rows)
        # Grafana 可以直接用对象或转成 [{"Building":..., "total_kW":...}]
        return JSONResponse(agg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hourly/latest", response_model=List[DataRecord])
async def hourly_latest():
    """最近一小时的全部原始数据"""
    try:
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # 设置一个较大的值来获取所有记录
        max_records = 10000  # 假设一小时内的记录不会超过这个数量
        
        rows = await run_in_threadpool(fetch_by_time_range, one_hour_ago, now, max_records)
        processed_rows = _process_raw_data(rows)
        
        print(f"Debug - 最近一小时获取记录数: {len(processed_rows)}")
        
        return processed_rows
    except Exception as e:
        print(f"Error in hourly_latest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hourly/summary")
async def hourly_summary():
    """最近一小时 → 按楼栋统计累计有功功率(kW)。"""
    try:
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # 设置一个较大的值来获取所有记录
        max_records = 10000  # 假设一小时内的记录不会超过这个数量
        
        rows = await run_in_threadpool(fetch_by_time_range, one_hour_ago, now, max_records)
        agg = _aggregate_by_building(rows)
        
        print(f"Debug - 最近一小时汇总记录数: {len(rows)}")
        
        return JSONResponse(agg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/daily/latest", response_model=List[DataRecord])
async def daily_latest():
    """最近一天的全部原始数据"""
    try:
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        # 设置一个较大的值来获取所有记录
        max_records = 50000  # 假设一天内的记录不会超过这个数量
        
        rows = await run_in_threadpool(fetch_by_time_range, one_day_ago, now, max_records)
        processed_rows = _process_raw_data(rows)
        
        print(f"Debug - 最近一天获取记录数: {len(processed_rows)}")
        
        return processed_rows
    except Exception as e:
        print(f"Error in daily_latest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/daily/summary")
async def daily_summary():
    """最近一天 → 按楼栋统计累计有功功率(kW)。"""
    try:
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        # 设置一个较大的值来获取所有记录
        max_records = 50000  # 假设一天内的记录不会超过这个数量
        
        rows = await run_in_threadpool(fetch_by_time_range, one_day_ago, now, max_records)
        agg = _aggregate_by_building(rows)
        
        print(f"Debug - 最近一天汇总记录数: {len(rows)}")
        
        return JSONResponse(agg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/weekly/latest", response_model=List[DataRecord])
async def weekly_latest():
    """最近一周的全部原始数据"""
    try:
        now = datetime.now()
        one_week_ago = now - timedelta(days=7)
        
        # 设置一个较大的值来获取所有记录
        max_records = 200000  # 假设一周内的记录不会超过这个数量
        
        rows = await run_in_threadpool(fetch_by_time_range, one_week_ago, now, max_records)
        processed_rows = _process_raw_data(rows)
        
        print(f"Debug - 最近一周获取记录数: {len(processed_rows)}")
        
        return processed_rows
    except Exception as e:
        print(f"Error in weekly_latest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/weekly/summary")
async def weekly_summary():
    """最近一周 → 按楼栋统计累计有功功率(kW)。"""
    try:
        now = datetime.now()
        one_week_ago = now - timedelta(days=7)
        
        # 设置一个较大的值来获取所有记录
        max_records = 200000  # 假设一周内的记录不会超过这个数量
        
        rows = await run_in_threadpool(fetch_by_time_range, one_week_ago, now, max_records)
        agg = _aggregate_by_building(rows)
        
        print(f"Debug - 最近一周汇总记录数: {len(rows)}")
        
        return JSONResponse(agg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monthly/latest", response_model=List[DataRecord])
async def monthly_latest():
    """最近一个月的全部原始数据"""
    try:
        now = datetime.now()
        one_month_ago = now - timedelta(days=30)  # 使用30天作为一个月的近似值
        
        # 设置一个较大的值来获取所有记录
        max_records = 500000  # 假设一个月内的记录不会超过这个数量
        
        rows = await run_in_threadpool(fetch_by_time_range, one_month_ago, now, max_records)
        processed_rows = _process_raw_data(rows)
        
        print(f"Debug - 最近一个月获取记录数: {len(processed_rows)}")
        
        return processed_rows
    except Exception as e:
        print(f"Error in monthly_latest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monthly/summary")
async def monthly_summary():
    """最近一个月 → 按楼栋统计累计有功功率(kW)。"""
    try:
        now = datetime.now()
        one_month_ago = now - timedelta(days=30)  # 使用30天作为一个月的近似值
        
        # 设置一个较大的值来获取所有记录
        max_records = 500000  # 假设一个月内的记录不会超过这个数量
        
        rows = await run_in_threadpool(fetch_by_time_range, one_month_ago, now, max_records)
        agg = _aggregate_by_building(rows)
        
        print(f"Debug - 最近一个月汇总记录数: {len(rows)}")
        
        return JSONResponse(agg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/custom/latest", response_model=List[DataRecord])
async def custom_latest(
    start_date: str = Query(..., description="开始日期（格式：YYYY-MM-DD 或 YYYY-MM-DDThh:mm:ss）"),
    end_date: str = Query(..., description="结束日期（格式：YYYY-MM-DD 或 YYYY-MM-DDThh:mm:ss）")
):
    """自定义时间范围的全部原始数据（最长7天）"""
    try:
        start_dt, end_dt = await _validate_date_range(start_date, end_date)
        
        # 调试信息
        print(f"Debug - 查询时间范围: {start_dt} 到 {end_dt}")
        
        # 设置一个较大的值来获取所有记录
        max_records = 200000  # 假设7天内的记录不会超过这个数量
        
        rows = await run_in_threadpool(fetch_by_time_range, start_dt, end_dt, max_records)
        
        # 调试信息
        if rows:
            print(f"Debug - 查询到数据行数: {len(rows)}")
            if len(rows) > 0:
                print(f"Debug - 第一行数据时间: {rows[0].get('timestamp1', 'N/A')}")
                print(f"Debug - 最后一行数据时间: {rows[-1].get('timestamp1', 'N/A')}")
        else:
            print("Debug - 未查询到数据")
            
        processed_rows = _process_raw_data(rows)
        
        return processed_rows
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Error in custom_latest endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/custom/summary")
async def custom_summary(
    start_date: str = Query(..., description="开始日期（格式：YYYY-MM-DD 或 YYYY-MM-DDThh:mm:ss）"),
    end_date: str = Query(..., description="结束日期（格式：YYYY-MM-DD 或 YYYY-MM-DDThh:mm:ss）")
):
    """自定义时间范围 → 按楼栋统计累计有功功率(kW)（最长7天）。"""
    try:
        start_dt, end_dt = await _validate_date_range(start_date, end_date)
        
        # 调试信息
        print(f"Debug - 汇总查询时间范围: {start_dt} 到 {end_dt}")
        
        # 设置一个较大的值来获取所有记录
        max_records = 200000  # 假设7天内的记录不会超过这个数量
        
        rows = await run_in_threadpool(fetch_by_time_range, start_dt, end_dt, max_records)
        
        # 调试信息
        if rows:
            print(f"Debug - 汇总查询到数据行数: {len(rows)}")
        else:
            print("Debug - 汇总未查询到数据")
            
        agg = _aggregate_by_building(rows)
        
        return JSONResponse(agg)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", include_in_schema=False)
def root():
    return {"msg": "Welcome! Visit /docs for Swagger UI."} 