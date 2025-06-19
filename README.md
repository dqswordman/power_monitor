# MUT Power Monitor – 最小后端

## 快速开始
```bash
# 安装依赖
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 运行
uvicorn app.main:app --reload --port 8000
```

## 可用 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/latest?n=5` | 最近 5 行原始记录 |
| GET | `/summary?n=5` | 最近 5 行楼栋功率汇总 |

打开 http://localhost:8000/docs 查看 Swagger UI。

---

### ✨ 使用提示
- **Grafana** 可通过 `JSON API` 插件直接调用 `/summary`，每 5-10 s 轮询即可实时刷新。  
- 若想改成 **数据库直连**，只需重写 `pma_client.fetch_latest`，调用 `pymysql` 或 `asyncmy` 即可，其它文件不动。  

至此，一个**无需 .env、一次即可跑通**的后端项目已完整给出。复制粘贴对应文件后即可运行 🚀 