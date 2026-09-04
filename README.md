# GimbalFlow Backend Architecture

Full-stack production backend architecture for GimbalFlow AI Video & Motion Director Platform.
Unified high-performance **Python (FastAPI)** backend replacing multi-tier Node.js gateway and microservice setup.

## Technology Stack

- **Python (FastAPI + Uvicorn)**: Unified asynchronous REST API for API Gateway, Auth, Database ORM/pooling, Admin CMS, Machine Learning pipelines, and 3D camera trajectory generation.
- **Redis**: In-memory data store handling real-time task queues, caching, and write-buffering (with built-in in-memory fallback).
- **MySQL**: Relational production database with strict table partitioning for high concurrency (with built-in in-memory fallback).

## Directory Structure

```
gimbalflow backend/
├── database/
│   └── schema.sql            # MySQL schema DDL & initial seed data
├── python-server/            # Unified FastAPI Server (Port 5000)
│   ├── app/
│   │   ├── config/           # MySQL pool, Redis queue/cache, Settings, and Admin Scrypt Auth
│   │   ├── routers/          # REST API route controllers (auth, user, projects, assets, presets, explore, generation, admin)
│   │   ├── ml/               # Machine learning engine & camera vector generator
│   │   ├── data/             # Persistent JSON stores (hero-cards.json, gallery.json)
│   │   ├── uploads/          # Uploaded media (hero section videos / photos)
│   │   └── main.py           # FastAPI entrypoint (Port 5000)
│   ├── .env                  # Server environment variables
│   ├── run.py                # Server execution script
│   ├── Dockerfile            # Production container definition
│   └── requirements.txt      # Python dependencies
├── node-server/              # (Archived) Legacy Node.js Express server
├── python-ml-service/        # (Archived) Legacy standalone ML microservice
└── docker-compose.yml        # Multi-container orchestration (MySQL, Redis, Python Backend)
```

## Running the Backend

### Option 1: Direct Python Execution
```bash
cd python-server
pip install -r requirements.txt
python run.py
```
The server will start on `http://localhost:5000` with Swagger docs available at `http://localhost:5000/docs`.

### Option 2: Docker Compose (All Services: MySQL, Redis, FastAPI Backend)
```bash
docker-compose up -d --build
```
