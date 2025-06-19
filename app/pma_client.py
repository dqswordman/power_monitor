#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/pma_client.py  · 兼容你已验证可行的抓取方式
"""

import re, requests
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from . import config

def _get_token(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    inp  = soup.find("input", {"name": "token"})
    if not inp or not inp.get("value"):
        raise RuntimeError("❌ 无法找到 token，检查 phpMyAdmin 版本/路径")
    return inp["value"]

def _parse_table(html: str) -> List[Dict]:
    soup  = BeautifulSoup(html, "lxml")

    # 若 SQL 报错，phpMyAdmin 会在 div.alert-danger 中显示
    err = soup.find("div", class_=re.compile(r"alert.*danger"))
    if err:
        raise RuntimeError("❌ SQL 执行失败：" + err.get_text(strip=True))

    table = soup.find("table", class_=re.compile(r"(table_results|dataTable|table\-data)"))
    if not table:
        raise RuntimeError("❌ 未找到结果表格，phpMyAdmin 结构已变")

    # 表头
    header = [th.get_text(strip=True) for th in table.find("tr").find_all("th")]
    if not header:
        raise RuntimeError("❌ 无法解析表头")

    # 数据行
    records: List[Dict] = []
    for tr in table.find_all("tr")[1:]:          # 跳过首行表头
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if cells:
            records.append(dict(zip(header, cells)))
    return records

def fetch_latest(limit: int = config.DEFAULT_LIMIT) -> List[Dict]:
    sql = (f"SELECT * FROM {config.TABLE_NAME} "
           f"ORDER BY {config.ORDER_BY_COLUMN} DESC LIMIT {limit};")

    s = requests.Session()
    s.headers.update({
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"
    })

    # ① 登录
    login_url = f"{config.PMA_BASE}/index.php"
    r = s.get(login_url, timeout=config.TIMEOUT, verify=config.VERIFY_SSL)
    token = _get_token(r.text)

    r = s.post(login_url, data={
        "pma_username": config.PMA_USERNAME,
        "pma_password": config.PMA_PASSWORD,
        "server": 1,
        "target": "index.php",
        "token": token,
    }, timeout=config.TIMEOUT, verify=config.VERIFY_SSL)
    if "phpMyAdmin" not in r.text:
        raise RuntimeError("❌ 登录失败，请检查用户名/密码")

    token = _get_token(r.text)

    # ② 执行 SQL
    r = s.post(f"{config.PMA_BASE}/sql.php", data={
        "server": 1,
        "db": config.DATABASE_NAME,
        "table": config.TABLE_NAME,
        "token": token,
        "sql_query": sql,
        "pos": 0,
    }, timeout=config.TIMEOUT, verify=config.VERIFY_SSL)
    r.raise_for_status()

    return _parse_table(r.text)

def fetch_by_time_range(start_time: datetime, end_time: datetime, limit: int = config.DEFAULT_LIMIT) -> List[Dict]:
    """
    根据时间范围获取数据
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        limit: 最大返回行数
    
    Returns:
        符合时间范围的数据列表
    """
    # 格式化时间为 MySQL 格式
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 优化 SQL 查询，确保获取从大于等于开始日期到小于等于结束日期的数据
    sql = (f"SELECT * FROM {config.TABLE_NAME} "
           f"WHERE {config.ORDER_BY_COLUMN} >= '{start_time_str}' AND {config.ORDER_BY_COLUMN} <= '{end_time_str}' "
           f"ORDER BY {config.ORDER_BY_COLUMN} DESC LIMIT {limit};")

    s = requests.Session()
    s.headers.update({
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"
    })

    # ① 登录
    login_url = f"{config.PMA_BASE}/index.php"
    r = s.get(login_url, timeout=config.TIMEOUT, verify=config.VERIFY_SSL)
    token = _get_token(r.text)

    r = s.post(login_url, data={
        "pma_username": config.PMA_USERNAME,
        "pma_password": config.PMA_PASSWORD,
        "server": 1,
        "target": "index.php",
        "token": token,
    }, timeout=config.TIMEOUT, verify=config.VERIFY_SSL)
    if "phpMyAdmin" not in r.text:
        raise RuntimeError("❌ 登录失败，请检查用户名/密码")

    token = _get_token(r.text)

    # ② 执行 SQL
    r = s.post(f"{config.PMA_BASE}/sql.php", data={
        "server": 1,
        "db": config.DATABASE_NAME,
        "table": config.TABLE_NAME,
        "token": token,
        "sql_query": sql,
        "pos": 0,
    }, timeout=config.TIMEOUT, verify=config.VERIFY_SSL)
    r.raise_for_status()

    return _parse_table(r.text) 