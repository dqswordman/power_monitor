from typing import List, Dict, Optional
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from datetime import datetime, timedelta
from collections import OrderedDict
import math

from . import config
from .pma_client import fetch_latest, fetch_by_time_range
from .models import DataRecord

DESC = """
MUT Power Monitor · Demo API

* `/latest`             — 最近 N 行原始数据（用于测试和异常检测）
* `/summary`            — 最近 N 行楼栋有功功率汇总
* `/hourly/tests`       — 最近一小时的全部原始数据
* `/hourly/summary`     — 最近一小时楼栋有功功率汇总
* `/daily/tests`        — 最近一天的全部原始数据
* `/daily/summary`      — 最近一天楼栋有功功率汇总
* `/weekly/tests`       — 最近一周的全部原始数据
* `/weekly/summary`     — 最近一周楼栋有功功率汇总
* `/monthly/tests`      — 最近一个月的全部原始数据
* `/monthly/summary`    — 最近一个月楼栋有功功率汇总
* `/custom/tests`       — 自定义时间范围的全部原始数据（最长7天）
* `/custom/summary`     — 自定义时间范围的楼栋有功功率汇总（最长7天）
* `/daily-stats/summary` — 最近10天内每天按楼栋统计的有功功率汇总
* `/half-hourly/summary` — 24小时内每半小时的楼栋有功功率汇总
* `/test/half-hourly/summary` — 测试API：指定时间24小时内每半小时的楼栋有功功率汇总
"""

app = FastAPI(
    title="MUT Power Monitor API",
    version="0.5.0",
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
    """最近 N 行记录（用于测试和异常检测）"""
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


@app.get("/hourly/tests", response_model=List[DataRecord])
async def hourly_tests():
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
        print(f"Error in hourly_tests endpoint: {str(e)}")
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


@app.get("/daily/tests", response_model=List[DataRecord])
async def daily_tests():
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
        print(f"Error in daily_tests endpoint: {str(e)}")
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


@app.get("/weekly/tests", response_model=List[DataRecord])
async def weekly_tests():
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
        print(f"Error in weekly_tests endpoint: {str(e)}")
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


@app.get("/monthly/tests", response_model=List[DataRecord])
async def monthly_tests():
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
        print(f"Error in monthly_tests endpoint: {str(e)}")
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


@app.get("/custom/tests", response_model=List[DataRecord])
async def custom_tests(
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
        print(f"Error in custom_tests endpoint: {str(e)}")
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


@app.get("/daily-stats/summary")
async def daily_stats_summary():
    """最近10天内每天按楼栋统计的有功功率汇总"""
    try:
        now = datetime.now()
        ten_days_ago = now - timedelta(days=10)
        
        # 按天统计结果
        daily_stats = OrderedDict()
        
        for day_offset in range(10):
            # 计算每天的开始和结束时间
            current_day = now - timedelta(days=day_offset)
            
            # 当天的零点
            day_start = current_day.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # 如果是当天，结束时间为当前时间；否则为当天最后一秒
            if day_offset == 0:
                day_end = now
            else:
                day_end = day_start + timedelta(days=1, seconds=-1)  # 23:59:59
            
            # 日期格式化为 YYYY-MM-DD 用作 key
            day_key = day_start.strftime("%Y-%m-%d")
            
            # 设置一个较大的值来获取所有记录
            max_records = 50000  # 假设一天内的记录不会超过这个数量
            
            # 查询该天的数据
            rows = await run_in_threadpool(fetch_by_time_range, day_start, day_end, max_records)
            
            # 计算该天的汇总数据
            agg = _aggregate_by_building(rows)
            
            # 添加到结果中
            daily_stats[day_key] = {
                "date": day_key,
                "summary": agg,
                "record_count": len(rows)
            }
            
            print(f"Debug - 日期: {day_key}, 记录数: {len(rows)}")
        
        return JSONResponse(daily_stats)
    except Exception as e:
        print(f"Error in daily_stats_summary endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/half-hourly/summary")
async def half_hourly_summary():
    """获取当前时间往前推算24小时内每半个小时的功率汇总数据"""
    try:
        # 获取当前时间
        now = datetime.now()
        
        # 计算整点或半点时间
        if now.minute < 30:
            last_half_hour = now.replace(minute=0, second=0, microsecond=0)
        else:
            last_half_hour = now.replace(minute=30, second=0, microsecond=0)
            
        # 24小时前的时间（48个半小时）
        day_ago = last_half_hour - timedelta(days=1)
        
        result = {}
        
        # 为每个半小时时间段生成数据
        current_time = day_ago
        while current_time <= last_half_hour:
            # 计算时间段结束时间
            end_time = current_time + timedelta(minutes=30)
            
            # 获取该时间段的数据
            rows = await run_in_threadpool(fetch_by_time_range, current_time, end_time, 10000)
            
            # 汇总该时间段的数据
            agg = _aggregate_by_building(rows)
            
            # 使用时间段的结束时间作为键
            time_key = end_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 存储结果
            result[time_key] = {
                "end_time": time_key,
                "summary": agg
            }
            
            # 移动到下一个半小时时间段
            current_time = end_time
        
        # 添加当前时间的数据
        if now > last_half_hour:
            rows = await run_in_threadpool(fetch_by_time_range, last_half_hour, now, 10000)
            agg = _aggregate_by_building(rows)
            current_time_key = now.strftime("%Y-%m-%d %H:%M:%S")
            result[current_time_key] = {
                "end_time": current_time_key,
                "summary": agg
            }
        
        return JSONResponse(result)
    except Exception as e:
        print(f"Error in half_hourly_summary endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test/half-hourly/summary")
async def test_half_hourly_summary(
    test_time: str = Query(..., description="测试时间（格式：YYYY-MM-DD 或 YYYY-MM-DDThh:mm:ss 或 YYYY-MM-DD hh:mm:ss）")
):
    """测试API：根据指定时间往前推算24小时内每半个小时的功率汇总数据"""
    try:
        # 解析输入时间
        if "T" not in test_time and " " not in test_time and len(test_time.split("-")) == 3:
            test_dt = datetime.fromisoformat(f"{test_time}T00:00:00")
        else:
            test_dt = datetime.fromisoformat(test_time.replace(" ", "T") if " " in test_time else test_time)
        
        print(f"Debug - 测试时间: {test_dt}")
        
        # 计算整点或半点时间
        if test_dt.minute < 30:
            last_half_hour = test_dt.replace(minute=0, second=0, microsecond=0)
        else:
            last_half_hour = test_dt.replace(minute=30, second=0, microsecond=0)
            
        print(f"Debug - 最近半小时整点: {last_half_hour}")
        
        # 24小时前的时间（48个半小时）
        day_ago = last_half_hour - timedelta(days=1)
        
        print(f"Debug - 24小时前时间: {day_ago}")
        
        result = {}
        
        # 为每个半小时时间段生成数据
        current_time = day_ago
        while current_time <= last_half_hour:
            # 计算时间段结束时间
            end_time = current_time + timedelta(minutes=30)
            
            print(f"Debug - 正在查询时间范围: {current_time} 至 {end_time}")
            
            # 获取该时间段的数据
            rows = await run_in_threadpool(fetch_by_time_range, current_time, end_time, 10000)
            
            print(f"Debug - 该时间段获取记录数: {len(rows)}")
            
            # 汇总该时间段的数据
            agg = _aggregate_by_building(rows)
            
            print(f"Debug - 该时间段数据汇总: {agg}")
            
            # 使用时间段的结束时间作为键
            time_key = end_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 存储结果
            result[time_key] = {
                "end_time": time_key,
                "summary": agg
            }
            
            # 移动到下一个半小时时间段
            current_time = end_time
        
        # 添加当前时间的数据
        if test_dt > last_half_hour:
            print(f"Debug - 正在查询最后时间段: {last_half_hour} 至 {test_dt}")
            
            rows = await run_in_threadpool(fetch_by_time_range, last_half_hour, test_dt, 10000)
            
            print(f"Debug - 最后时间段获取记录数: {len(rows)}")
            
            agg = _aggregate_by_building(rows)
            
            print(f"Debug - 最后时间段数据汇总: {agg}")
            
            current_time_key = test_dt.strftime("%Y-%m-%d %H:%M:%S")
            result[current_time_key] = {
                "end_time": current_time_key,
                "summary": agg
            }
        
        print(f"Debug - 总共生成时间段数: {len(result)}")
        
        return JSONResponse(result)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="日期格式无效，请使用ISO格式：YYYY-MM-DD 或 YYYY-MM-DDThh:mm:ss 或 YYYY-MM-DD hh:mm:ss"
        )
    except Exception as e:
        print(f"Error in test_half_hourly_summary endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", include_in_schema=False)
def root():
    return {"msg": "Welcome! Visit /docs for Swagger UI."} 