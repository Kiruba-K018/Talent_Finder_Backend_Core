# Backend Core Deployment Guide

## Overview

The Talent Finder Backend Core service is a FastAPI application that runs on Python 3.12. It integrates with PostgreSQL, MongoDB, and ChromaDB. Deployment options include local Docker Compose, Google Cloud Run, and Kubernetes.

## Quick Start - Local Docker Compose

### Prerequisites

- Docker and Docker Compose installed
- 4GB RAM minimum available
- Port availability: 8000 (API), 5433 (PostgreSQL), 27017 (MongoDB)

### Local Deployment

1. Clone repository and navigate to Backend Core directory:
```bash
cd Talent_Finder_Backend/Talent_Finder_Backend_Core
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your configuration:
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=talentfinder
MONGO_USER=mongo
MONGO_PASSWORD=your_secure_password
MONGO_DB=talentfinder
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
ACCESS_SECRET=generate_32_char_secret_key
REFRESH_SECRET=generate_32_char_secret_key
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

4. Start all services:
```bash
docker-compose up -d
```

5. Verify deployment:
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8000/health/ready

# Check database connectivity
docker-compose logs app | grep "Database connected"
```

The API will be available at `http://localhost:8000` with OpenAPI documentation at `http://localhost:8000/docs`.

## Docker Configuration

### Image Details

**Base Image:** `python:3.12-slim`

**Dependencies:**
- FastAPI web framework
- SQLAlchemy with psycopg3 for PostgreSQL
- Motor for MongoDB async driver
- Pydantic for data validation
- ChromaDB client for vector storage
- JWT for authentication

### Dockerfile

The provided `Dockerfile` creates an optimized image:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy and install Python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY .env* ./

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "src.api.rest.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Image Size Optimization

- Uses `python:3.12-slim` base (reduces size by 60% vs. standard image)
- Installs without cache (`--no-cache-dir`)
- Single layer for dependencies
- Not included in image: development packages, source control, test files

## Docker Compose Services

### Service Configuration

#### PostgreSQL (Port 5433)

```yaml
image: postgres:15-alpine
volumes:
  - postgres_data:/var/lib/postgresql/data
environment:
  - POSTGRES_USER (required)
  - POSTGRES_PASSWORD (required)
  - POSTGRES_DB (default: talentfinder)
healthcheck: pg_isready every 10 seconds, timeout 5 seconds, 5 retries
```

**Storage:** Data persists in `postgres_data` volume (survives container restarts)

**Access:** `postgresql://user:password@postgres:5432/talentfinder` from within network

#### MongoDB (Port 27017)

```yaml
image: mongo:7
volumes:
  - mongodb_data:/data/db
  - ./src/data/migrations/mongo-init.js:/docker-entrypoint-initdb.d/init.js
environment:
  - MONGO_INITDB_ROOT_USERNAME (required)
  - MONGO_INITDB_ROOT_PASSWORD (required)
  - MONGO_INITDB_DATABASE (default: talentfinder)
healthcheck: mongosh ping every 10 seconds
```

**Storage:** Data persists in `mongodb_data` volume

**Initialization:** Runs `mongo-init.js` on first start to create collections and indexes

**Access:** `mongodb://user:password@mongodb:27017/talentfinder?authSource=admin` from within network

#### FastAPI App (Port 8000)

**Startup:** Waits for PostgreSQL and MongoDB health checks to pass

**Volumes:**
- Source code (auto-reload in development)
- ChromaDB cache directory

**Environment:** Loads from `.env` file and overrides for container networking

## Environment Configuration

### Core Settings

```
APP_PORT=8000                    # FastAPI server port
DATABASE_URL=                    # If set, overrides derived database_url
PYTHONUNBUFFERED=1              # Real-time log output
```

### PostgreSQL Settings

```
POSTGRES_USER=postgres           # Database user
POSTGRES_PASSWORD=              # User password (required)
POSTGRES_DB=talentfinder        # Database name
POSTGRES_PORT=5432              # Internal port (5433 mapped on host)
POSTGRES_SSL_MODE=prefer        # SSL mode preference
POSTGRES_POOL_SIZE=3            # Max connections (reduced for Cloud SQL)
POSTGRES_POOL_MIN_SIZE=1        # Min connections
```

**Connection URL Format:**
```
postgresql://user:password@host:port/dbname?sslmode=prefer
```

### MongoDB Settings

```
MONGO_USER=mongo                # MongoDB user
MONGO_PASSWORD=                 # User password (required)
MONGO_HOST=mongodb              # Connection host
MONGO_PORT=27017                # Connection port
MONGO_DB=talentfinder           # Database name
MONGO_AUTHSOURCE=admin          # Authentication database

# Optional: MongoDB Atlas
ATLAS_CONNECTION_STRING=        # mongodb+srv://... URI for Atlas
```

**Local Connection:** `mongodb://user:password@mongodb:27017/talentfinder?authSource=admin`

**Atlas Connection:** Provide full `mongodb+srv://...` URI to `ATLAS_CONNECTION_STRING`

### Authentication Settings

```
ACCESS_SECRET=                  # 32+ character secret for access tokens
REFRESH_SECRET=                 # 32+ character secret for refresh tokens
ALGORITHM=HS256                 # JWT algorithm
ACCESS_EXPIRE_MIN=60            # Access token lifetime in minutes
REFRESH_EXPIRE_MIN=10080        # Refresh token lifetime (7 days in minutes)
```

**Generate Secrets:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### API Keys

```
GROQ_API_KEY=                   # Groq API key for LLM
OPENAI_API_KEY=                 # OpenAI API key (optional)
CEREBRAS_API_KEY=               # Cerebras API key (optional)
```

### CORS Configuration

```
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

Space or comma-separated list of allowed origins for cross-origin requests.

### Email Settings (Optional)

```
EMAIL_HOST=localhost            # SMTP server
EMAIL_PORT=587                  # SMTP port
EMAIL_USER=                     # SMTP authentication user
EMAIL_PASSWORD=                 # SMTP authentication password
EMAIL_FROM=                     # Sender email address
EMAIL_DEFAULT_RECIPIENT=        # Default recipient for test emails
```

## Google Cloud Run Deployment

### Prerequisites

- Google Cloud account with active project
- `gcloud` CLI installed and configured
- Docker credential helper configured
- Service account with Cloud Run, Cloud SQL, and IAM permissions

### Deployment Script

Use the provided `deploy.sh`:

```bash
#!/bin/bash

PROJECT_ID="gwx-internship-01"
REGION="us-east1"
SERVICE_NAME="talentfinder-backend-core"
GAR_REPO="us-east1-docker.pkg.dev/$PROJECT_ID/gwx-gar-intern-01"
IMAGE="$GAR_REPO/talentfinder-backend-core:latest"

# Cloud SQL connection
DB_URL="postgresql+psycopg://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE"

# MongoDB Atlas
MONGODB_ATLAS_URI="mongodb+srv://user:password@cluster.mongodb.net/dbname"

# Build and push image
docker build -t $IMAGE .
docker push $IMAGE

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE \
  --region=$REGION \
  --platform=managed \
  --port=8000 \
  --memory=2Gi \
  --max-instances=2 \
  --min-instances=0 \
  --timeout=600 \
  --no-cpu-throttling \
  --service-account=SERVICE_ACCOUNT_EMAIL \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE \
  --set-env-vars="DB_URL=$DB_URL,ATLAS_CONNECTION_STRING=$MONGODB_ATLAS_URI"
```

### Deployment Configuration

**Memory & CPU:**
- Memory: 2Gi (2GB) - suitable for typical workloads
- CPU: Fully allocated (not throttled)
- Timeout: 600 seconds (10 minutes for long-running operations)

**Scaling:**
- Min instances: 0 (cold starts to save cost)
- Max instances: 2 (prevents runaway costs)

**Cloud SQL Integration:**
- Uses Cloud SQL Proxy via Unix socket
- Connection format: `/cloudsql/PROJECT:REGION:INSTANCE`
- Service account must have Cloud SQL Client role

### Environment Variables for Cloud Run

```
DB_URL=postgresql+psycopg://user:password@/database?host=/cloudsql/PROJECT:REGION:INSTANCE
ATLAS_CONNECTION_STRING=mongodb+srv://user:password@cluster.mongodb.net/database
ACCESS_SECRET=your_secret_key
REFRESH_SECRET=your_secret_key
GROQ_API_KEY=your_groq_key
CORS_ORIGINS=https://yourdomain.com
```

### Post-Deployment Verification

```bash
# Get service URL
gcloud run services describe talentfinder-backend-core \
  --region=us-east1 \
  --format='value(status.url)'

# Test health endpoint
curl https://YOUR_SERVICE_URL/health

# View logs
gcloud run services logs read talentfinder-backend-core \
  --region=us-east1 \
  --limit=50
```


## Backup and Recovery

### PostgreSQL Backup

**Automated Backup (Docker):**

```bash
# Backup current database
docker-compose exec postgres pg_dump -U postgres talentfinder > backup.sql

# List available backups
ls -lh backup*.sql
```

**Restore from Backup:**

```bash
# Stop the application
docker-compose stop app sourcing

# Restore database
docker-compose exec -T postgres psql -U postgres talentfinder < backup.sql

# Restart services
docker-compose up -d app sourcing
```

**Cloud SQL Automated Backups:**

- Automatic backups: Enabled daily at off-peak times
- Retention: 30 days
- Location: Multi-region for disaster recovery

**Manual Backup for Cloud SQL:**

```bash
# Export to Cloud Storage
gcloud sql export sql talentfinder-instance \
  gs://backup-bucket/talentfinder-$(date +%Y%m%d).sql \
  --database=talentfinder
```

**Restore from Cloud SQL Backup:**

```bash
# Import from Cloud Storage
gcloud sql import sql talentfinder-instance \
  gs://backup-bucket/talentfinder-20240319.sql \
  --database=talentfinder
```

### MongoDB Backup

**Automated Backup (Docker):**

```bash
# Create backup directory
mkdir -p backups

# Backup MongoDB
docker-compose exec mongo mongodump --out=/backups/$(date +%Y%m%d_%H%M%S)

# Compress backup
tar -czf mongodb_backup_$(date +%Y%m%d).tar.gz backups/
```

**Restore from MongoDB Backup:**

```bash
# Extract backup
tar -xzf mongodb_backup_20240319.tar.gz

# Restore data
docker-compose exec -T mongo mongorestore backups/20240319_120000/
```

**MongoDB Atlas Backups:**

- Automatic backups: Every 6 hours
- Retention: 30 days (free tier), longer with paid plans
- Point-in-time recovery: Supported with sharded clusters
## Scaling Considerations

### Horizontal Scaling

**Docker Compose:**
- Limited to single machine resources
- Not recommended for production multi-instance scaling
- Use for development and single-server deployments

**Cloud Run:**
- Auto-scales from 0 to max-instances based on traffic
- Default: min=0, max=2
- Increase max-instances for higher throughput

Update `deploy.sh`:
```bash
--max-instances=5      # Higher traffic capacity
```

### Database Connection Pooling

**PostgreSQL Pool Settings:**

```
POSTGRES_POOL_SIZE=3           # Max connections per instance
POSTGRES_POOL_MIN_SIZE=1       # Min idle connections
```

Reduced from defaults (10/20) for Cloud SQL proxy limitations.

**Connection Calculation:**

For N instances: Total connections = N × POSTGRES_POOL_SIZE

Example: 5 replicas × 3 pool size = 15 total connections

**Adjust for capacity:**

```bash
# Cloud SQL: Ensure connection limit > instances × pool_size
# PostgreSQL default: 100 connections, typically sufficient
```

### MongoDB Scaling

**Docker Compose:** Single node only

**MongoDB Atlas:**
- Cluster tier: M2 (minimum for production)
- Replica set: Automatic with sharded clusters
- Auto-scaling: Storage available on paid tiers

### Performance Optimization

**Caching:**
- ChromaDB caches locally in container
- Consider Redis for distributed caching

**Database Indexing:**
- MongoDB: Automatically indexed on _id
- PostgreSQL: Verify indexes on frequently queried columns

**Request Optimization:**
- Implement pagination on list endpoints
- Use database projection to limit returned fields
- Cache static configuration in memory

## Monitoring and Logging

### Health Endpoints

**Liveness Check (is service running?):**
```bash
curl http://localhost:8000/health
```

**Readiness Check (can service handle requests?):**
```bash
curl http://localhost:8000/health/ready
```

These are used by Kubernetes probes and load balancers.

### Logs

**Docker Compose:**
```bash
docker-compose logs -f app        # Follow app logs
docker-compose logs app --tail=50 # Last 50 lines
```

**Cloud Run:**
```bash
gcloud run logs read talentfinder-backend-core --limit=100
```

**Kubernetes:**
```bash
kubectl logs -f deployment/backend-core -n talentfinder
kubectl logs -l app=backend-core -n talentfinder --all-containers=true
```

### Metrics

Expose Prometheus metrics (if instrumented):
```
GET /metrics
```

## Troubleshooting

### Database Connection Issues

**Symptom:** Service fails to start with "Database connection refused"

**Solution:**
1. Verify database service is healthy: `docker-compose ps`
2. Check credentials in .env file
3. Test database connectivity: `docker-compose exec postgres psql -U postgres -c "SELECT 1"`
4. Review logs: `docker-compose logs app`

### Out of Memory

**Symptom:** Container crashes with OOMKilled

**Solution:**
1. Increase memory limit in docker-compose.yml
2. Check for memory leaks: Monitor memory usage over time
3. Reduce POSTGRES_POOL_SIZE if multiple instances

### Slow Queries

**Symptom:** API endpoints respond slowly

**Solution:**
1. Check database query logs
2. Verify database indexes exist
3. Monitor connection pool saturation
4. Consider query optimization or caching

## Production Checklist

- [ ] Database backups automated and tested
- [ ] Environment variables secured (use secret management)
- [ ] CORS origins restricted to specific domains
- [ ] JWT secrets rotated regularly
- [ ] Health checks configured and verified
- [ ] Database connection pooling optimized for scale
- [ ] CloudSQL/MongoDB Atlas backups enabled
- [ ] Monitoring and alerting configured
- [ ] Log retention policies set
- [ ] Rate limiting implemented for API
- [ ] HTTPS/TLS certificates valid
- [ ] All external API keys secured
