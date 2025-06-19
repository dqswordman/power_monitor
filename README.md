# MUT Power Monitor API

A ready-to-use minimal project for monitoring and managing power data. Built with FastAPI, providing RESTful API interfaces.

## 📋 Project Overview

### Features
- 🔌 **Real-time Data Retrieval** - Fetch latest power data from phpMyAdmin database
- 📊 **Data Aggregation** - Calculate cumulative active power by building
- 🚀 **Out-of-the-box Ready** - No environment variables needed, centralized configuration
- 📈 **Grafana Friendly** - Direct support for Grafana JSON API plugin
- 🔧 **Easy to Extend** - Modular design for easy feature expansion
- ⏱️ **Time-based Data** - Query data by hour, day, week, or custom time range

### API Endpoints

| Method | Path | Parameters | Description |
|--------|------|------------|-------------|
| GET | `/latest` | `n` (optional, default 5) | Get latest N raw records |
| GET | `/summary` | `n` (optional, default 5) | Get building power summary for latest N records |
| GET | `/hourly/latest` | `n` (optional, default 5) | Get latest N raw records from the last hour |
| GET | `/hourly/summary` | `n` (optional, default 5) | Get building power summary for the last hour |
| GET | `/daily/latest` | `n` (optional, default 5) | Get latest N raw records from the last day |
| GET | `/daily/summary` | `n` (optional, default 5) | Get building power summary for the last day |
| GET | `/weekly/latest` | `n` (optional, default 5) | Get latest N raw records from the last week |
| GET | `/weekly/summary` | `n` (optional, default 5) | Get building power summary for the last week |
| GET | `/custom/latest` | `start_date`, `end_date`, `n` (optional, default 5) | Get latest N raw records from custom time range (max 7 days) |
| GET | `/custom/summary` | `start_date`, `end_date`, `n` (optional, default 5) | Get building power summary for custom time range (max 7 days) |
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

# Get latest 5 records from the last hour
curl "http://localhost:8000/hourly/latest?n=5"

# Get latest 5 records from the last day
curl "http://localhost:8000/daily/latest?n=5"

# Get latest 5 records from the last week
curl "http://localhost:8000/weekly/latest?n=5"

# Get latest 5 records from a custom time range (max 7 days)
curl "http://localhost:8000/custom/latest?start_date=2023-06-01&end_date=2023-06-07&n=5"
```

### Get Summary Data
```bash
# Get building power summary for latest 5 records
curl "http://localhost:8000/summary?n=5"

# Get building power summary for the last hour
curl "http://localhost:8000/hourly/summary?n=5"

# Get building power summary for the last day
curl "http://localhost:8000/daily/summary?n=5"

# Get building power summary for the last week
curl "http://localhost:8000/weekly/summary?n=5"

# Get building power summary for a custom time range (max 7 days)
curl "http://localhost:8000/custom/summary?start_date=2023-06-01&end_date=2023-06-07&n=5"
```

Response example:
```json
{
  "Building A": 150.5,
  "Building B": 89.2,
  "Building C": 234.1
}
```

### Custom Time Range Format

For custom time range endpoints, use one of these date formats:
- Simple date: `YYYY-MM-DD` (e.g., `2023-06-01`)
  - If you use only date without time, the system will automatically use:
    - 00:00:00 (beginning of day) for start date
    - 23:59:59 (end of day) for end date
- Date with time (ISO format): `YYYY-MM-DDThh:mm:ss` (e.g., `2023-06-01T14:30:00`)
- Date with time (standard format): `YYYY-MM-DD hh:mm:ss` (e.g., `2023-06-01 14:30:00`)

Note: The time range cannot exceed 7 days, or the API will return an error.

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

5. **Custom Date Range Errors**
   - Ensure dates are in one of the supported formats:
     - `YYYY-MM-DD` (e.g., 2023-06-01)
     - `YYYY-MM-DDThh:mm:ss` (e.g., 2023-06-01T14:30:00)
     - `YYYY-MM-DD hh:mm:ss` (e.g., 2023-06-01 14:30:00)
   - For date-only format, the system will automatically use 00:00:00 for start date and 23:59:59 for end date
   - Verify that the time range does not exceed 7 days
   - Confirm that end_date is after start_date
   - Check server logs for detailed error messages and debug information

## 📝 Changelog

### v0.2.0 (2024-07-XX)
- ✨ Added time-based API endpoints (hourly, daily, weekly)
- 🚀 Implemented custom date range queries
- 📊 Enhanced data retrieval capabilities
- 🔧 Improved code reusability and organization

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