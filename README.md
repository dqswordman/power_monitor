# MUT Power Monitor API

一个开箱即用的最小可运行项目，用于监控和管理电力数据。基于 FastAPI 构建，提供 RESTful API 接口。

## 📋 项目概述

### 功能特性
- 🔌 **实时数据获取** - 从 phpMyAdmin 数据库获取最新电力数据
- 📊 **数据聚合** - 按楼栋统计累计有功功率
- 🚀 **开箱即用** - 无需环境变量，配置集中管理
- 📈 **Grafana 友好** - 支持 Grafana JSON API 插件直接调用
- 🔧 **易于扩展** - 模块化设计，便于功能扩展

### API 接口

| 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|
| GET | `/latest` | `n` (可选，默认5) | 获取最近 N 条原始记录 |
| GET | `/summary` | `n` (可选，默认5) | 获取最近 N 条记录的楼栋功率汇总 |
| GET | `/` | - | 欢迎页面 |
| GET | `/docs` | - | Swagger UI 文档 |

## 🏗️ 项目结构

```
power_monitor/
├── app/
│   ├── __init__.py          # 包标识文件
│   ├── config.py            # 全局配置常量
│   ├── models.py            # Pydantic 数据模型
│   ├── pma_client.py        # phpMyAdmin 数据抓取逻辑
│   └── main.py              # FastAPI 应用入口
├── requirements.txt         # Python 依赖包
└── README.md               # 项目文档
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 网络连接（访问 phpMyAdmin）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd power_monitor
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv .venv
   ```

3. **激活虚拟环境**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

5. **配置数据库连接**
   
   编辑 `app/config.py` 文件，修改以下配置：
   ```python
   # phpMyAdmin 相关
   PMA_BASE      = "http://203.188.24.230/phpmyadmin"  # 您的 phpMyAdmin 地址
   PMA_USERNAME  = "root"                              # 数据库用户名
   PMA_PASSWORD  = "qweasd"                            # 数据库密码
   DATABASE_NAME = "mut_supermap_datalog"              # 数据库名
   TABLE_NAME    = "data_value"                        # 表名
   ```

6. **启动服务**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

7. **访问应用**
   - API 文档：http://localhost:8000/docs
   - 欢迎页面：http://localhost:8000/
   - 测试接口：http://localhost:8000/latest?n=5

## 📖 API 使用说明

### 获取原始数据
```bash
# 获取最近 5 条记录
curl "http://localhost:8000/latest?n=5"

# 获取最近 10 条记录
curl "http://localhost:8000/latest?n=10"
```

### 获取汇总数据
```bash
# 获取最近 5 条记录的楼栋功率汇总
curl "http://localhost:8000/summary?n=5"
```

响应示例：
```json
{
  "Building A": 150.5,
  "Building B": 89.2,
  "Building C": 234.1
}
```

## 🔧 配置说明

### 主要配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `PMA_BASE` | phpMyAdmin 基础 URL | `http://203.188.24.230/phpmyadmin` |
| `PMA_USERNAME` | 数据库用户名 | `root` |
| `PMA_PASSWORD` | 数据库密码 | `qweasd` |
| `DATABASE_NAME` | 数据库名称 | `mut_supermap_datalog` |
| `TABLE_NAME` | 数据表名称 | `data_value` |
| `ORDER_BY_COLUMN` | 排序字段 | `timestamp` |
| `VERIFY_SSL` | SSL 验证 | `False` |
| `TIMEOUT` | 请求超时时间 | `30` 秒 |
| `DEFAULT_LIMIT` | 默认返回记录数 | `5` |
| `MAX_LIMIT` | 最大返回记录数 | `100` |

## 📊 数据模型

### DataRecord 模型
```python
class DataRecord(BaseModel):
    id: int                    # 记录ID
    timestamp: str             # 时间戳
    volt1: float              # 电压1
    volt2: float              # 电压2
    volt3: float              # 电压3
    current1: float           # 电流1
    current2: float           # 电流2
    current3: float           # 电流3
    power1: float             # 功率1
    power2: float             # 功率2
    power3: float             # 功率3
    energy1: float            # 电能1
    energy2: float            # 电能2
    energy3: float            # 电能3
    Building: str             # 楼栋名称
    Floor: Optional[int]      # 楼层（可选）
```

## 🔗 Grafana 集成

### 使用 JSON API 插件

1. 在 Grafana 中安装 "JSON API" 数据源插件
2. 配置数据源：
   - URL: `http://localhost:8000/summary?n=10`
   - 查询间隔：5-10 秒
3. 创建面板，选择 JSON API 数据源
4. 配置查询以显示楼栋功率数据

### 示例查询
```json
{
  "Building A": 150.5,
  "Building B": 89.2,
  "Building C": 234.1
}
```

## 🛠️ 开发指南

### 添加新的 API 端点

1. 在 `app/main.py` 中添加新的路由函数
2. 在 `app/models.py` 中定义相应的数据模型
3. 在 `app/pma_client.py` 中添加数据获取逻辑

### 修改数据库连接

如需改为直接数据库连接，只需重写 `app/pma_client.py` 中的 `fetch_latest` 函数：

```python
import pymysql

def fetch_latest(limit: int = config.DEFAULT_LIMIT) -> List[Dict]:
    connection = pymysql.connect(
        host='your_host',
        user=config.PMA_USERNAME,
        password=config.PMA_PASSWORD,
        database=config.DATABASE_NAME
    )
    
    with connection.cursor() as cursor:
        sql = f"SELECT * FROM {config.TABLE_NAME} ORDER BY {config.ORDER_BY_COLUMN} DESC LIMIT {limit}"
        cursor.execute(sql)
        results = cursor.fetchall()
        
    connection.close()
    return results
```

## 🐛 故障排除

### 常见问题

1. **Import 错误**
   ```bash
   # 确保在虚拟环境中
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **数据库连接失败**
   - 检查 `app/config.py` 中的配置
   - 确认 phpMyAdmin 服务可访问
   - 验证用户名密码正确

3. **API 返回 500 错误**
   - 检查服务器日志
   - 确认数据库表结构正确
   - 验证字段名匹配

4. **数据验证错误**
   - 检查 `app/models.py` 中的字段定义
   - 确认数据库字段名与模型别名匹配

## 📝 更新日志

### v0.1.0 (2024-01-XX)
- ✨ 初始版本发布
- 🚀 实现基础 API 功能
- 📊 支持数据聚合
- 🔧 模块化架构设计

### 最新更新
- 🔧 修复 ResponseValidationError 问题
- 📝 改进数据模型验证
- 🛠️ 增强错误处理
- 📚 完善项目文档

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 项目 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com

---

**注意**: 请确保在生产环境中使用前，修改默认的数据库凭据和配置。 