# MUT Power Monitor API

A ready-to-use minimal project for monitoring and managing power data. Built with FastAPI, providing RESTful API interfaces.

## 📋 Project Overview

### Features
- 🔌 **Real-time Data Retrieval** - Fetch latest power data from phpMyAdmin database
- 📊 **Data Aggregation** - Calculate cumulative active power by building
- 🚀 **Out-of-the-box Ready** - No environment variables needed, centralized configuration
- 📈 **Grafana Friendly** - Direct support for Grafana JSON API plugin
- 🔧 **Easy to Extend** - Modular design for easy feature expansion
- ⏱️ **Time-based Data** - Query data by hour, day, week, month, or custom time range
- 💯 **Complete Data Access** - Time-based queries return all matching records without limits
- 📅 **Daily Statistics** - Get daily summaries for the past 10 days
- ⏲️ **Half-hourly Data** - Get 24-hour data divided into 30-minute intervals with timestamps

### API Endpoints

| Method | Path | Parameters | Description |
|--------|------|------------|-------------|
| GET | `/latest` | `n` (optional, default 5) | Get latest N raw records (for testing and anomaly detection) |
| GET | `/summary` | `n` (optional, default 5) | Get building power summary for latest N records |
| GET | `/hourly/tests` | none | Get all raw records from the last hour |
| GET | `/hourly/summary` | none | Get building power summary for the last hour |
| GET | `/daily/tests` | none | Get all raw records from the last day |
| GET | `/daily/summary` | none | Get building power summary for the last day |
| GET | `/weekly/tests` | none | Get all raw records from the last week |
| GET | `/weekly/summary` | none | Get building power summary for the last week |
| GET | `/monthly/tests` | none | Get all raw records from the last month |
| GET | `/monthly/summary` | none | Get building power summary for the last month |
| GET | `/custom/tests` | `start_date`, `end_date` | Get all raw records from custom time range (max 7 days) |
| GET | `/custom/summary` | `start_date`, `end_date` | Get building power summary for custom time range (max 7 days) |
| GET | `/daily-stats/summary` | none | Get daily building power summaries for the last 10 days |
| GET | `/half-hourly/summary` | none | Get 24-hour data in 30-minute intervals from current time |
| GET | `/test/half-hourly/summary` | `test_time` | Test API: Get 24-hour data in 30-minute intervals from specified time |
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
└── README.md                # Project documentation
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
# Get latest 5 records (for testing and anomaly detection, limited by n)
curl "http://localhost:8000/latest?n=5"

# Get latest 10 records (for testing and anomaly detection, limited by n)
curl "http://localhost:8000/latest?n=10"

# Get all records from the last hour
curl "http://localhost:8000/hourly/tests"

# Get all records from the last day
curl "http://localhost:8000/daily/tests"

# Get all records from the last week
curl "http://localhost:8000/weekly/tests"

# Get all records from the last month
curl "http://localhost:8000/monthly/tests"

# Get all records from a custom time range (max 7 days)
curl "http://localhost:8000/custom/tests?start_date=2023-06-01&end_date=2023-06-07"
```

### Get Summary Data
```bash
# Get building power summary for latest 5 records (limited by n)
curl "http://localhost:8000/summary?n=5"

# Get building power summary for all records from the last hour
curl "http://localhost:8000/hourly/summary"

# Get building power summary for all records from the last day
curl "http://localhost:8000/daily/summary"

# Get building power summary for all records from the last week
curl "http://localhost:8000/weekly/summary"

# Get building power summary for all records from the last month
curl "http://localhost:8000/monthly/summary"

# Get building power summary for all records from a custom time range (max 7 days)
curl "http://localhost:8000/custom/summary?start_date=2023-06-01&end_date=2023-06-07"

# Get daily building power summaries for the last 10 days
curl "http://localhost:8000/daily-stats/summary"

# Get 24-hour data in 30-minute intervals from current time
curl "http://localhost:8000/half-hourly/summary"

# Test API: Get 24-hour data in 30-minute intervals from a specified time
curl "http://localhost:8000/test/half-hourly/summary?test_time=2023-06-10T15:45:00"
```

### Response Examples

#### Regular Summary Response
```json
{
  "Building A": 150.5,
  "Building B": 89.2,
  "Building C": 234.1
}
```

#### Daily Stats Summary Response
```json
{
  "2023-06-10": {
    "date": "2023-06-10",
    "summary": {
      "Building A": 145.2,
      "Building B": 82.1,
      "Building C": 215.7
    },
    "record_count": 287
  },
  "2023-06-09": {
    "date": "2023-06-09",
    "summary": {
      "Building A": 152.3,
      "Building B": 91.4,
      "Building C": 224.9
    },
    "record_count": 312
  },
  ... (8 more days)
}
```

#### Half-hourly Summary Response
```json
{
  "2023-06-09 12:30:00": {
    "end_time": "2023-06-09 12:30:00",
    "summary": {
      "Building A": 142.8,
      "Building B": 85.3,
      "Building C": 219.7
    }
  },
  "2023-06-09 13:00:00": {
    "end_time": "2023-06-09 13:00:00",
    "summary": {
      "Building A": 148.6,
      "Building B": 88.2,
      "Building C": 221.3
    }
  },
  ... (more 30-minute intervals)
}
```

### Half-hourly Data Format

The half-hourly APIs (`/half-hourly/summary` and `/test/half-hourly/summary`) provide power data for 24 hours divided into 30-minute intervals:

- Each API returns exactly 48 complete half-hour intervals (24 hours) plus one partial interval
- The system finds the nearest half-hour mark (either on the hour or at 30 minutes past)
- For each interval, the response includes the end timestamp and power summary by building
- The final interval contains data from the last half-hour mark to the current/specified time

For the test endpoint (`/test/half-hourly/summary`), provide a timestamp using one of these formats:
- Simple date: `YYYY-MM-DD` (defaults to 00:00:00 for that day)
- ISO format: `YYYY-MM-DDThh:mm:ss`
- Standard format: `YYYY-MM-DD hh:mm:ss`

Example: `/test/half-hourly/summary?test_time=2023-06-10T15:45:00`

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
| `DEFAULT_LIMIT` | Default record limit (for `/latest` and `/summary`) | `5` |
| `MAX_LIMIT` | Maximum record limit (for `/latest` and `/summary`) | `100` |

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
   - URL: `http://localhost:8000/summary?n=10` or `http://localhost:8000/hourly/summary`
   - For daily statistics: `http://localhost:8000/daily-stats/summary`
   - For 24-hour half-hourly data: `http://localhost:8000/half-hourly/summary`
   - Query interval: 5-10 seconds
3. Create panel and select JSON API data source
4. Configure query to display building power data

### Example Queries
```json
// Regular summary
{
  "Building A": 150.5,
  "Building B": 89.2,
  "Building C": 234.1
}

// Daily stats summary (access data for specific days)
{
  "2023-06-10": {
    "summary": {
      "Building A": 145.2
    }
  }
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

### v0.5.0 (2025-06-21-7:00)
- ✨ Added half-hourly power data APIs:
  - `/half-hourly/summary`: 24-hour data in 30-minute intervals from current time
  - `/test/half-hourly/summary`: Test API with specified time and debugging output
- 🔄 Each API returns 48 complete half-hour intervals plus one partial interval
- 📊 Enhanced data format with end timestamps and building summaries
- 📝 Improved documentation and examples

### v0.4.0 (2025-06-20-7:00)
- 🔄 Renamed all time-based data endpoints from `/*/latest` to `/*/tests`
- ✨ Added `/daily-stats/summary` endpoint for 10-day daily summaries
- 🎯 Repurposed `/latest` endpoint specifically for testing and anomaly detection
- 📊 Enhanced response formats with more detailed information

### v0.3.0 (2025-06-19-22:00)
- 🚀 Removed record limits for time-based API endpoints
- ✨ Added monthly data endpoints for last 30 days
- 📊 Improved custom date range handling
- 🔍 Enhanced debugging information

### v0.2.0 (2025-06-19-17:30)
- ✨ Added time-based API endpoints (hourly, daily, weekly)
- 🚀 Implemented custom date range queries
- 📊 Enhanced data retrieval capabilities
- 🔧 Improved code reusability and organization

### v0.1.0 (2025-06-19-8:30)
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
- Email: dqswordman@gmail.com

