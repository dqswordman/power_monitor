from typing import List, Dict
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from . import config
from .pma_client import fetch_latest
from .models import DataRecord

DESC = """
MUT Power Monitor · Demo API

* `/latest`   — 最近 N 行原始数据  
* `/summary`  — 最近 N 行楼栋有功功率汇总
"""

app = FastAPI(
    title="MUT Power Monitor API",
    version="0.1.0",
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
        processed_rows = []
        for row in rows:
            # 确保所有必需字段都存在
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


@app.get("/", include_in_schema=False)
def root():
    return {"msg": "Welcome! Visit /docs for Swagger UI."} 