# Dump Truck Contract Finder API

FastAPI backend for finding and managing dump truck contract awards from state transportation departments.

## Features

- **Ingestion**: Placeholder modules for KYTC (Kentucky) and INDOT (Indiana) contract data
- **Scoring**: Rule-based scoring system using keyword matching
- **Database**: SQLite database with persistent storage at `/data/app.db`
- **API Endpoints**: RESTful API for managing contract leads

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── scoring.py           # Scoring logic
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── kytc.py          # KYTC ingestion (stub)
│   │   ├── indot.py         # INDOT ingestion (stub)
│   │   └── runner.py        # Ingestion orchestrator
│   └── api/
│       ├── __init__.py
│       └── routes.py        # API routes
├── tests/
│   ├── __init__.py
│   └── test_scoring.py      # Scoring function tests
├── requirements.txt
└── README.md
```

## Running with Docker

### Prerequisites

- Docker and Docker Compose installed
- The `/data` folder mounted as a persistent volume

### Using Docker Compose (Recommended)

Create a `docker-compose.yml` in the project root:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
    environment:
      - DATABASE_URL=sqlite:///data/app.db
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then run:

```bash
docker-compose up
```

### Using Docker Directly

```bash
# Build the image
docker build -t dump-truck-finder ./backend

# Run the container
docker run -p 8000:8000 -v $(pwd)/data:/data dump-truck-finder
```

### Development Container

If using a dev container, ensure:
- The `/data` volume is mounted
- Port 8000 is forwarded
- Dependencies are installed: `pip install -r requirements.txt`

Run the application:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Run Ingestion

```bash
curl -X POST http://localhost:8000/ingest/run
```

Response:
```json
{
  "kytc_count": 0,
  "indot_count": 0,
  "total_processed": 0,
  "total_upserted": 0
}
```

### Get Leads

Get all leads sorted by score:

```bash
curl http://localhost:8000/leads
```

Filter by state:

```bash
curl "http://localhost:8000/leads?state=KY"
```

Filter by status:

```bash
curl "http://localhost:8000/leads?status=new"
```

Filter by minimum score:

```bash
curl "http://localhost:8000/leads?min_score=20"
```

Combine filters:

```bash
curl "http://localhost:8000/leads?state=KY&status=new&min_score=15"
```

### Update Lead Status

```bash
curl -X POST http://localhost:8000/leads/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "contacted"}'
```

Available statuses: `new`, `contacted`, `ignored`, `converted`

## Testing

Run tests with pytest:

```bash
cd backend
pytest tests/
```

Run with verbose output:

```bash
pytest tests/ -v
```

## Database

The SQLite database is stored at `/data/app.db` (mounted persistent volume).

### Schema

The `contract_awards` table includes:
- `id`: Primary key
- `state`: State code (KY/IN)
- `letting_date`: Contract letting date
- `contract_id`: Contract identifier
- `awarded_to`: Company name
- `description`: Contract description
- `amount`: Contract amount (nullable)
- `source_url`: Source URL
- `score`: Relevance score (0+)
- `score_reasons`: JSON string of scoring reasons
- `status`: Status enum (new/contacted/ignored/converted)
- `created_at`: Timestamp
- `updated_at`: Timestamp

## Scoring System

The scoring system uses keyword matching with weighted scores:

- `dump truck`, `dumptruck`, `dump-truck`: 10 points
- `hauling`, `haul`: 8 points
- `earthwork`: 7 points
- `excavation`: 6 points
- `grading`: 6 points
- `fill`: 5 points
- `aggregate`, `gravel`: 5 points
- And more...

Bonus points are awarded when multiple relevant keywords are found.

## Development

### Adding New Ingestion Sources

1. Create a new module in `app/ingest/` (e.g., `newstate.py`)
2. Implement `ingest_newstate()` function returning raw contract data
3. Implement `normalize_newstate()` function to normalize to standard format
4. Add the ingestion call to `app/ingest/runner.py`

### Extending Scoring

Modify `KEYWORD_WEIGHTS` in `app/scoring.py` to add or adjust keyword weights.

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

