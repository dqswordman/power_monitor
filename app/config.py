"""
集中配置（不使用 .env）
"""

# phpMyAdmin
PMA_BASE      = "http://203.188.24.230/phpmyadmin"
PMA_USERNAME  = "root"
PMA_PASSWORD  = "qweasd"
DATABASE_NAME = "mut_supermap_datalog"
TABLE_NAME    = "data_value"

# ——关键修改：排序列——
ORDER_BY_COLUMN = "timestamp"   # 与线上字段保持一致

# 网络
VERIFY_SSL = False
TIMEOUT    = 30    # 秒

# API 默认
DEFAULT_LIMIT = 5
MAX_LIMIT     = 100
