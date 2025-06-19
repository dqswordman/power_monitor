# MUT Power Monitor API

A ready-to-use minimal project for monitoring and managing power data. Built with FastAPI, providing RESTful API interfaces.

## 📋 Project Overview

### Features
- 🔌 **Real-time Data Retrieval** - Fetch latest power data from phpMyAdmin database
- 📊 **Data Aggregation** - Calculate cumulative active power by building
- 🚀 **Out-of-the-box Ready** - No environment variables needed, centralized configuration
- 📈 **Grafana Friendly** - Direct support for Grafana JSON API plugin
- 🔧 **Easy to Extend** - Modular design for easy feature expansion

### API Endpoints

| Method | Path | Parameters | Description |
|--------|------|------------|-------------|
| GET | `/latest` | `n` (optional, default 5) | Get latest N raw records |
| GET | `/summary` | `n` (optional, default 5) | Get building power summary for latest N records |
| GET | `/` | - | Welcome page |
| GET | `/docs` | - | Swagger UI documentation |

## 🏗️ Project Structure

```
power_monitor/
├── app/
│   ├── __init__.py          # Package identifier
│   ├── config.py            # Global configuration constants
│   ├── models.py            # Pydantic data models
│   ├── pma_client.py        # phpMyAdmin data fetching logic
│   └── main.py              # FastAPI application entry point
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

## 🚀 Quick Start

### Requirements
- Python 3.8+
- Network connection (to access phpMyAdmin)

### Installation Steps

1. **Clone the project**
   ```bash
   git clone <repository-url>
   cd power_monitor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure database connection**
   
   Edit `app/config.py` file and modify the following configurations:
   ```python
   # phpMyAdmin settings
   PMA_BASE      = "http://203.188.24.230/phpmyadmin"  # Your phpMyAdmin URL
   PMA_USERNAME  = "root"                              # Database username
   PMA_PASSWORD  = "qweasd"                            # Database password
   DATABASE_NAME = "mut_supermap_datalog"              # Database name
   TABLE_NAME    = "data_value"                        # Table name
   ```

6. **Start the service**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

7. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Welcome Page: http://localhost:8000/
   - Test Endpoint: http://localhost:8000/latest?n=5

## 📖 API Usage

### Get Raw Data
```bash
# Get latest 5 records
curl "http://localhost:8000/latest?n=5"

# Get latest 10 records
curl "http://localhost:8000/latest?n=10"
```

### Get Summary Data
```bash
# Get building power summary for latest 5 records
curl "http://localhost:8000/summary?n=5"
```

Response example:
```json
{
  "Building A": 150.5,
  "Building B": 89.2,
  "Building C": 234.1
}
```

## 🔧 Configuration

### Main Configuration Items

| Config Item | Description | Default Value |
|-------------|-------------|---------------|
| `PMA_BASE` | phpMyAdmin base URL | `http://203.188.24.230/phpmyadmin` |
| `PMA_USERNAME` | Database username | `root` |
| `PMA_PASSWORD` | Database password | `qweasd` |
| `DATABASE_NAME` | Database name | `mut_supermap_datalog` |
| `TABLE_NAME` | Data table name | `data_value` |
| `ORDER_BY_COLUMN` | Sort column | `timestamp` |
| `VERIFY_SSL` | SSL verification | `False` |
| `TIMEOUT` | Request timeout | `30` seconds |
| `DEFAULT_LIMIT` | Default record limit | `5` |
| `MAX_LIMIT` | Maximum record limit | `100` |

## 📊 Data Models

### DataRecord Model
```python
class DataRecord(BaseModel):
    id: int                    # Record ID
    timestamp: str             # Timestamp
    volt1: float              # Voltage 1
    volt2: float              # Voltage 2
    volt3: float              # Voltage 3
    current1: float           # Current 1
    current2: float           # Current 2
    current3: float           # Current 3
    power1: float             # Power 1
    power2: float             # Power 2
    power3: float             # Power 3
    energy1: float            # Energy 1
    energy2: float            # Energy 2
    energy3: float            # Energy 3
    Building: str             # Building name
    Floor: Optional[int]      # Floor (optional)
```

## 🔗 Grafana Integration

### Using JSON API Plugin

1. Install "JSON API" data source plugin in Grafana
2. Configure data source:
   - URL: `http://localhost:8000/summary?n=10`
   - Query interval: 5-10 seconds
3. Create panel and select JSON API data source
4. Configure query to display building power data

### Example Query
```json
{
  "Building A": 150.5,
  "Building B": 89.2,
  "Building C": 234.1
}
```

## 🛠️ Development Guide

### Adding New API Endpoints

1. Add new route function in `app/main.py`
2. Define corresponding data model in `app/models.py`
3. Add data fetching logic in `app/pma_client.py`

### Modifying Database Connection

To switch to direct database connection, simply rewrite the `fetch_latest` function in `app/pma_client.py`:

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

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in virtual environment
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database Connection Failure**
   - Check configurations in `app/config.py`
   - Confirm phpMyAdmin service is accessible
   - Verify username and password are correct

3. **API Returns 500 Error**
   - Check server logs
   - Confirm database table structure is correct
   - Verify field names match

4. **Data Validation Errors**
   - Check field definitions in `app/models.py`
   - Confirm database field names match model aliases

## 📝 Changelog

### v0.1.0 (2024-01-XX)
- ✨ Initial version release
- 🚀 Implement basic API functionality
- 📊 Support data aggregation
- 🔧 Modular architecture design

### Latest Updates
- 🔧 Fix ResponseValidationError issues
- 📝 Improve data model validation
- 🛠️ Enhance error handling
- 📚 Complete project documentation

## 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 📞 Contact

For questions or suggestions, please contact:
- Project Issues: [GitHub Issues](https://github.com/your-repo/issues)
- Email: your-email@example.com

---

**Note**: Please ensure to modify default database credentials and configurations before using in production environment. 