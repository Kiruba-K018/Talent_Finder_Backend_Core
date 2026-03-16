# Talent_Finder_Backend_Core
The core backend services of the talentfinder - resume sourcing and shortlisting platform 
for candidate ingestion, resume parsing, profile enrichment, matching, and shortlist workflow orchestration.

## Overview

This service provides the core backend capabilities for the Talent Finder platform. It is intended to support scalable resume sourcing, candidate evaluation, recruiter workflows, and API integrations required for production deployments.

## Key Features

- Resume ingestion and processing
- Candidate profile normalization and enrichment
- Search, filtering, and shortlist workflows
- REST API support for internal and external consumers
- Authentication and authorization support
- Health checks and readiness endpoints
- Structured logging and observability hooks
- Environment-based configuration for local, staging, and production use

## Getting Started

### Prerequisites

Ensure the following are available before setup:

- Runtime for the backend service
- Package manager used by the project
- Database server
- Cache/message broker, if applicable
- Environment configuration file
- Access to required third-party APIs or storage providers

### Installation

```bash
git clone <repository-url>
cd Talent_Finder_Backend_Core
```

Install dependencies using the package manager configured for the project:

```bash
# example
npm install
# or
yarn install
# or
pip install -r requirements.txt
```

### Configuration

Create and configure environment variables before starting the service.

#### Example environment variables

```env
APP_ENV=development
PORT=8080
HOST=0.0.0.0

DATABASE_URL=<database-connection-string>
REDIS_URL=<redis-connection-string>

JWT_SECRET=<strong-secret>
CORS_ORIGIN=<allowed-origin>

LOG_LEVEL=info
```

Recommended practices:

- Do not commit secrets to source control
- Use separate values per environment
- Rotate secrets regularly
- Store production secrets in a secure secret manager


## API Reference

Base path example:

```http
/api/v1
```

### Health

#### Check service health

```http
GET /health
```

**Response**
```json
{
    "status": "ok"
}
```

### Authentication

#### Login or token issue endpoint

```http
POST /auth/login
```

**Request**
```json
{
    "email": "user@example.com",
    "password": "secure-password"
}
```

### Candidates

#### Create candidate record

```http
POST /candidates
```

#### Get candidate by ID

```http
GET /candidates/{id}
```

#### Search candidates

```http
GET /candidates?query=python&location=remote&experience=5
```

### Resumes

#### Upload resume

```http
POST /resumes
```

#### Parse or process resume

```http
POST /resumes/{id}/process
```

### Shortlists

#### Create shortlist

```http
POST /shortlists
```

#### Add candidate to shortlist

```http
POST /shortlists/{id}/candidates
```

> Update endpoint names, payloads, and response contracts to match the implemented API.

## Project Structure

```text
Talent_Finder_Backend_Core/
├── src/
│   ├── api/
│   ├── controllers/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   ├── middleware/
│   ├── config/
│   └── utils/
├── tests/
├── scripts/
├── docs/
├── .env.example
└── README.md
```
