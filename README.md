# GimbalFlow Backend Architecture

Full-stack production backend architecture for GimbalFlow AI Video & Motion Director Platform.

## Technology Stack

- **Python (FastAPI)**: Primary language for machine learning pipelines, model integration, 3D camera trajectory generation, and AI prompt enhancement.
- **Node.js / Express**: Lightweight server-side API Gateway for routing, user session state, and proxying ML jobs.
- **Redis**: In-memory data store handling real-time task queues, caching, and database write-buffering.
- **MySQL**: Relational production database with strict table partitioning for high concurrency.

## Directory Structure

```
gimbalflow backend/
├── database/
│   └── schema.sql            # MySQL schema DDL & initial seed data
├── node-server/
│   ├── src/
│   │   ├── config/           # MySQL pool & Redis queue/cache connection managers
│   │   ├── controllers/      # Express API controllers
│   │   ├── routes/           # Express router definitions
│   │   ├── services/         # FastAPI HTTP proxy client
│   │   └── server.js         # Entrypoint (Port 5000)
│   └── package.json
├── python-ml-service/
│   ├── config.py
│   ├── main.py               # FastAPI application (Port 8000)
│   ├── ml_pipeline.py        # ML engine & camera vector generator
│   ├── schemas.py            # Pydantic data models
│   └── requirements.txt
├── docker-compose.yml
└── package.json
```

## Running the Backend

### Option 1: Direct Node & Python Execution
1. **Start Python ML Service**:
   ```bash
   cd python-ml-service
   pip install -r requirements.txt
   python main.py
   ```
2. **Start Node.js API Gateway**:
   ```bash
   cd node-server
   npm install
   npm start
   ```

### Option 2: Docker Compose (All Services: MySQL, Redis, FastAPI, Express)
```bash
docker-compose up -d --build
```
