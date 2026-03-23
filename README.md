# Talent Finder - Backend Core Service

## Project Overview

The core backend service for the talent sourcing and shortlisting platform. This service provides scalable resume sourcing, candidate evaluation, recruiter workflows, and API integrations for candidate ingestion, resume parsing, profile enrichment, matching, and shortlist workflow orchestration.

### Key Features

- Semantic search with vector embeddings
- Candidate scoring and matching
- Shortlist workflow orchestration
- Multi-database support with optimized queries
- REST API with comprehensive documentation
- JWT-based authentication and role-based access control
- Health checks and observability hooks

## Architecture

The service uses a multi-database architecture for optimal performance:

- **PostgreSQL**: User authentication, role-based access control (RBAC), job posts, sourcing configurations, and transactional data
- **MongoDB**: Candidate scores, sourced candidates, and flexible schema documents
- **PgVector**: Vector embeddings for semantic search and AI-powered candidate matching

### Technology Stack

- **Framework**: FastAPI (Python 3.10+)
- **ORM**: SQLAlchemy (PostgreSQL)
- **Vector DB**: PgVector
- **Async**: AsyncIO with async database drivers
- **Validation**: Pydantic v2
- **API Documentation**: Swagger UI and ReDoc

## Setup Instructions (Local Development)

### Prerequisites

Before starting, ensure you have installed:

- Python 3.10+
- PostgreSQL 14+
- MongoDB 5+
- Git

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Talent_Finder_Backend/Talent_Finder_Backend_Core
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize databases**
   ```bash
   # Run PostgreSQL migrations
   alembic upgrade head
   
   # Seed initial data (optional)
   python src/utils/seed_database.py
   python src/utils/seed_mongodb.py
   ```

## Environment Variables Documentation

### Database Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/talent_finder` |
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017/talent_finder` |


### API Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `API_HOST` | Server host | `0.0.0.0` |
| `API_PORT` | Server port | `8000` |
| `API_VERSION` | API version prefix | `v1` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000,https://app.example.com` |

### Authentication & Security

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT token signing | `your-secret-key-min-32-chars` |
| `JWT_ALGORITHM` | JWT encryption algorithm | `HS256` |
| `JWT_EXPIRATION_HOURS` | Token expiration time in hours | `24` |

### External Services

| Variable | Description | Example |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq LLM API key | `gsk_xxxxxxxxxxxx` |
| `EMAIL_HOST` | SMTP server address | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP server port | `587` |
| `EMAIL_USER` | SMTP authentication username | `noreply@candidate.com` |
| `EMAIL_PASSWORD` | SMTP authentication password | `app-password` |
| `EMAIL_FROM` | Email sender address | `noreply@candidate.com` |

### Logging & Observability

| Variable | Description | Example |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log output format | `json` or `text` |

## Database Setup

### PostgreSQL Setup

1. **Create database**
   ```bash
   createdb talent_finder
   ```

2. **Access database**
   ```bash
   psql -U postgres -d talent_finder
   ```

### MongoDB Setup

1. **Create database and collections**
   ```bash
   mongo
   > use talent_finder
   > db.createCollection("sourced_candidates")
   > db.candidates.createIndex({ "email": 1 })
   ```

2. **Seed initial data**
   ```bash
   python src/utils/seed_mongodb.py
   ```


For development, ChromaDB operates in embedded mode by default in the `chroma_data/` directory.

## Running the Application

### Start Development Server

```bash
python -m src.main
```

The API will be available at `http://localhost:8000`

### Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Health Check

```bash
curl http://localhost:8000/health
```

### With Docker

```bash
docker-compose up -d
```

## API Endpoints Overview

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | User login with email and password |
| `POST` | `/api/v1/auth/logout` | User logout |
| `POST` | `/api/v1/auth/refresh` | Refresh JWT token |
| `POST` | `/api/v1/auth/register` | User registration (admin only) |

### Candidate Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/candidates` | List all candidates with filters |
| `POST` | `/api/v1/candidates` | Create new candidate |
| `GET` | `/api/v1/candidates/{id}` | Get candidate details |
| `PUT` | `/api/v1/candidates/{id}` | Update candidate information |
| `DELETE` | `/api/v1/candidates/{id}` | Delete candidate |
| `GET` | `/api/v1/candidates/search` | Search candidates with query |

### Resume Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/resumes/upload` | Upload and parse resume |
| `GET` | `/api/v1/resumes/{id}` | Get parsed resume data |
| `POST` | `/api/v1/resumes/{id}/process` | Trigger resume processing |

### Job Post Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/jobs` | List all job posts |
| `POST` | `/api/v1/jobs` | Create new job post |
| `GET` | `/api/v1/jobs/{id}` | Get job post details |
| `PUT` | `/api/v1/jobs/{id}` | Update job post |
| `DELETE` | `/api/v1/jobs/{id}` | Delete job post |

### Shortlist Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/shortlists` | List all shortlists |
| `POST` | `/api/v1/shortlists` | Create shortlist |
| `GET` | `/api/v1/shortlists/{id}` | Get shortlist details |
| `POST` | `/api/v1/shortlists/{id}/candidates` | Add candidate to shortlist |
| `DELETE` | `/api/v1/shortlists/{id}/candidates/{candidate_id}` | Remove candidate from shortlist |

### Sourcing Config Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/sourcing-config` | Get sourcing configuration |
| `POST` | `/api/v1/sourcing-config` | Create sourcing configuration |
| `PUT` | `/api/v1/sourcing-config/{id}` | Update sourcing configuration |

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check endpoint |
| `GET` | `/docs` | Swagger API documentation |
| `GET` | `/redoc` | ReDoc API documentation |

## Authentication Flow

### JWT Token-Based Authentication

1. **User Login**
   ```bash
   POST /api/v1/auth/login
   {
     "email": "user@example.com",
     "password": "secure_password"
   }
   ```
   
   **Response**
   ```json
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "token_type": "bearer",
     "expires_in": 86400,
     "user": {
       "id": "user-uuid",
       "email": "user@example.com",
       "role": "recruiter"
     }
   }
   ```

2. **Token Usage**
   - Include token in request header: `Authorization: Bearer <access_token>`
   - Token valid for 24 hours by default
   - Refresh token endpoint to get new token: `POST /api/v1/auth/refresh`

3. **Role-Based Access Control (RBAC)**
   - **Admin**: Full access to all endpoints
   - **Recruiter**: Access to jobs, candidates, and shortlists
   - **ViewOnly**: Read-only access to candidates and jobs

### Example Request with Token

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/candidates
```

## Deployment Guide

### Docker Deployment

1. **Build Docker image**
   ```bash
   docker build -t talent-finder-core:latest .
   ```

2. **Run with docker-compose**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f talent-finder-core
   ```

### Cloud Deployment (Google Cloud Run)

1. **Set environment variables**
   ```bash
   gcloud run deploy talent-finder-core \
     --image gcr.io/project-id/talent-finder-core:latest \
     --platform managed \
     --region us-central1 \
     --set-env-vars DATABASE_URL="...",MONGODB_URL="..." \
     --allow-unauthenticated
   ```

2. **Configure Cloud SQL Proxy** for PostgreSQL connectivity

3. **Set up Cloud Storage** for resume uploads

### Production Checklist

- [ ] Environment variables configured securely (use Secret Manager)
- [ ] Database backups configured
- [ ] CORS origins restricted to production domains
- [ ] HTTPS enabled (automatic with Cloud Run)
- [ ] Logging and monitoring configured
- [ ] Rate limiting enabled
- [ ] Database migrations tested and applied
- [ ] API documentation deployed
- [ ] Health checks configured
- [ ] Auto-scaling configured

## Troubleshooting

### Database Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Verify DATABASE_URL in .env
# Format: postgresql://user:password@host:port/database

# Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine('YOUR_DATABASE_URL'); engine.connect()"
```

### MongoDB Connection Issues

**Problem**: `pymongo.errors.ServerSelectionTimeoutError`

**Solution**:
```bash
# Check MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# Verify MONGODB_URL in .env
# Format: mongodb://user:password@host:port/database

# Test connection
python -c "from pymongo import MongoClient; client = MongoClient('YOUR_MONGODB_URL'); print(client.admin.command('ping'))"
```

### Import/Module Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Ensure you're in the correct directory
cd Talent_Finder_Backend/Talent_Finder_Backend_Core

# Reinstall package in editable mode
pip install -e .

# Or run with module syntax
python -m src.main
```

### Common Errors Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `CORS error` | Origin not in CORS_ORIGINS | Add origin to `.env` CORS_ORIGINS list |
| `401 Unauthorized` | Invalid or expired token | Refresh token or login again |
| `422 Unprocessable Entity` | Invalid request data | Check request schema in `/docs` |
| `500 Internal Server Error` | Server error | Check logs: `docker-compose logs -f` |
| `Connection timeout` | Service unavailable | Verify all services are running |

## Support & Documentation

- **API Documentation**: http://localhost:8000/docs
- **Configuration**: Check `src/config/settings.py`
- **Issues**: Create an issue on GitHub
