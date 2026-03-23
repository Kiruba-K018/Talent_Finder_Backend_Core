# Talent Finder Backend Core API Documentation

## Base URL

```
http://localhost:8000
https://api.talentfinder.com
```

## API Version

All endpoints are prefixed with `/api/v1` unless otherwise noted.

## Table of Contents

1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
   - [Authentication](#authentication-endpoints)
   - [Users](#users-endpoints)
   - [Organizations](#organizations-endpoints)
   - [Job Posts](#job-posts-endpoints)
   - [Candidate Shortlist](#candidate-shortlist-endpoints)
   - [Sourced Candidates](#sourced-candidates-endpoints)
   - [Sourcing Configuration](#sourcing-configuration-endpoints)
   - [Role & Permissions](#role--permissions-endpoints)
   - [Source Runs](#source-runs-endpoints)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [Status Codes](#status-codes)

## Authentication

### Bearer Token Authentication

All protected endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Obtaining Tokens

Tokens are obtained by logging in via the `/auth/login` endpoint. A refresh token is also provided to obtain new access tokens without re-authenticating.

### Token Rotation

Access tokens expire after a configurable duration (default: 24 hours). Use the `/auth/refresh` endpoint to obtain a new access token using the refresh token.

### Role-Based Access Control

Different endpoints require different roles:
- **Admin** (role_id: 1): Full system access
- **Recruiter** (role_id: 2): Manage job posts and candidate shortlists
- **View Only**: Read-only access to candidates and jobs

## Endpoints

### Authentication Endpoints

#### Login
```
POST /api/v1/auth/login
```

**Description:** Authenticate user and obtain access tokens.

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `400 Bad Request`: Invalid request format

---

#### Register
```
POST /api/v1/auth/register
```

**Description:** Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "message": "User registered successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**
- `400 Bad Request`: User already exists or invalid input
- `422 Unprocessable Entity`: Validation error

---

#### Refresh Token
```
POST /api/v1/auth/refresh
```

**Description:** Obtain a new access token using the refresh token.

**Cookie/Header:** Requires valid `refresh_token` in cookie or header

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired refresh token

---

#### Logout
```
POST /api/v1/auth/logout
```

**Description:** Invalidate the current session and refresh token.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

---

#### Forgot Password
```
POST /api/v1/auth/forgot-password
```

**Description:** Request password reset via OTP sent to email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "OTP sent to your email"
}
```

**Error Responses:**
- `404 Not Found`: User not found
- `500 Internal Server Error`: Email service unavailable

---

#### Verify OTP
```
POST /api/v1/auth/verify-otp
```

**Description:** Verify OTP received via email.

**Request Body:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response:** `200 OK`
```json
{
  "message": "OTP verified successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid or expired OTP
- `404 Not Found`: User not found

---

#### Reset Password
```
POST /api/v1/auth/reset-password
```

**Description:** Reset password using verified OTP.

**Request Body:**
```json
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewSecurePassword123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid OTP or weak password
- `404 Not Found`: User not found

---

### Users Endpoints

#### Create User
```
POST /api/v1/users
```

**Description:** Create a new user account. Admin only.

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "SecurePassword123",
  "name": "Jane Doe",
  "role_id": 2,
  "org_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:** `201 Created`
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440001",
  "email": "newuser@example.com",
  "name": "Jane Doe",
  "role_id": 2,
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-03-19T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Email already exists or invalid input
- `400 Bad Request`: Insufficient permissions

---

#### List Users
```
GET /api/v1/users
```

**Description:** Retrieve all users in the system.

**Authentication:** Required

**Query Parameters:**
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `role_id` (optional): Filter by role ID
- `org_id` (optional): Filter by organization ID

**Response:** `200 OK`
```json
[
  {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "role_id": 2,
    "org_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-03-19T10:30:00Z"
  }
]
```

---

#### Get User
```
GET /api/v1/users/{user_id}
```

**Description:** Retrieve user details by ID.

**Authentication:** Required

**Path Parameters:**
- `user_id` (required): UUID of the user

**Response:** `200 OK`
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "role_id": 2,
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-03-19T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: User not found

---

#### Update User
```
PUT /api/v1/users/{user_id}
```

**Description:** Update user details. Admin only.

**Authentication:** Required (Admin)

**Path Parameters:**
- `user_id` (required): UUID of the user

**Request Body:**
```json
{
  "name": "John Smith",
  "role_id": 3
}
```

**Response:** `200 OK`
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Smith",
  "role_id": 3,
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-03-19T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: User not found
- `400 Bad Request`: Invalid input

---

### Organizations Endpoints

#### Create Organization
```
POST /organizations
```

**Description:** Create a new organization. Admin only.

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "org_name": "Acme Corporation",
  "org_logo": "https://example.com/logo.png"
}
```

**Response:** `201 Created`
```json
{
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "org_name": "Acme Corporation",
  "org_logo": "https://example.com/logo.png",
  "created_at": "2024-03-19T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input

---

#### List Organizations
```
GET /organizations
```

**Description:** Retrieve all organizations.

**Authentication:** Required

**Query Parameters:**
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
[
  {
    "org_id": "550e8400-e29b-41d4-a716-446655440000",
    "org_name": "Acme Corporation",
    "org_logo": "https://example.com/logo.png",
    "created_at": "2024-03-19T10:30:00Z"
  }
]
```

---

#### Get Organization
```
GET /organizations/{org_id}
```

**Description:** Retrieve organization details by ID.

**Authentication:** Required

**Path Parameters:**
- `org_id` (required): UUID of the organization

**Response:** `200 OK`
```json
{
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "org_name": "Acme Corporation",
  "org_logo": "https://example.com/logo.png",
  "created_at": "2024-03-19T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Organization not found

---

#### Update Organization
```
PUT /organizations/{org_id}
```

**Description:** Update organization details. Admin only.

**Authentication:** Required (Admin)

**Path Parameters:**
- `org_id` (required): UUID of the organization

**Request Body:**
```json
{
  "org_name": "Acme Inc",
  "org_logo": "https://example.com/new-logo.png"
}
```

**Response:** `200 OK`
```json
{
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "org_name": "Acme Inc",
  "org_logo": "https://example.com/new-logo.png",
  "created_at": "2024-03-19T10:30:00Z"
}
```

---

### Job Posts Endpoints

#### List Job Posts
```
GET /api/v1/jobpost
```

**Description:** Retrieve all active job posts with pagination.

**Authentication:** Required

**Query Parameters:**
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (active, closed, draft, paused)
- `created_by` (optional): Filter by creator user ID
- `location` (optional): Filter by location

**Response:** `200 OK`
```json
{
  "job_posts": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "job_title": "Senior Backend Engineer",
      "description": "We are looking for a senior backend engineer...",
      "min_experience": 5,
      "max_experience": 10,
      "min_educational_qualifications": ["Bachelor's in CS"],
      "job_type": "Full-time",
      "required_skills": ["Python", "FastAPI", "PostgreSQL"],
      "preferred_skills": ["Kubernetes", "AWS"],
      "location_preference": "Remote",
      "status": "active",
      "no_of_candidates_required": 3,
      "created_by": "550e8400-e29b-41d4-a716-446655440001",
      "version": 1
    }
  ]
}
```

---

#### Create Job Post
```
POST /api/v1/jobpost
```

**Description:** Create a new job post. Recruiter and Admin only.

**Authentication:** Required (Recruiter)

**Request Body:**
```json
{
  "job_title": "Senior Backend Engineer",
  "job_description": "We are looking for a senior backend engineer with expertise in Python and microservices architecture...",
  "min_experience": 5,
  "max_experience": 10,
  "min_education_qualifications": ["Bachelor's in Computer Science"],
  "location_preference": "Remote",
  "job_type": "Full-time",
  "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "preferred_skills": ["Kubernetes", "AWS", "CI/CD"],
  "no_of_candidates_required": 3
}
```

**Response:** `201 Created`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_title": "Senior Backend Engineer",
  "description": "We are looking for a senior backend engineer...",
  "min_experience": 5,
  "max_experience": 10,
  "min_educational_qualifications": "Bachelor's in CS",
  "job_type": "Full-time",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "preferred_skills": ["Kubernetes", "AWS"],
  "location_preference": "Remote",
  "status": "active",
  "no_of_candidates_required": 3,
  "created_by": "550e8400-e29b-41d4-a716-446655440001",
  "version": 1
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input
- `403 Forbidden`: Insufficient permissions

---

#### Get Job Post
```
GET /api/v1/jobpost/{job_id}
```

**Description:** Retrieve job post details by ID.

**Authentication:** Required

**Path Parameters:**
- `job_id` (required): UUID of the job post

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_title": "Senior Backend Engineer",
  "description": "We are looking for a senior backend engineer...",
  "min_experience": 5,
  "max_experience": 10,
  "min_educational_qualifications": "Bachelor's in CS",
  "job_type": "Full-time",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "preferred_skills": ["Kubernetes", "AWS"],
  "location_preference": "Remote",
  "status": "active",
  "no_of_candidates_required": 3,
  "created_by": "550e8400-e29b-41d4-a716-446655440001",
  "version": 1
}
```

**Error Responses:**
- `404 Not Found`: Job post not found

---

#### Get Job Post Version
```
GET /api/v1/jobpost/{job_id}/version/{version}
```

**Description:** Retrieve a specific version of a job post.

**Authentication:** Required

**Path Parameters:**
- `job_id` (required): UUID of the job post
- `version` (required): Version number

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_title": "Senior Backend Engineer",
  "description": "We are looking for a senior backend engineer...",
  "min_experience": 5,
  "max_experience": 10,
  "min_educational_qualifications": "Bachelor's in CS",
  "job_type": "Full-time",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "preferred_skills": ["Kubernetes", "AWS"],
  "location_preference": "Remote",
  "status": "active",
  "no_of_candidates_required": 3,
  "created_by": "550e8400-e29b-41d4-a716-446655440001",
  "version": 1
}
```

**Error Responses:**
- `404 Not Found`: Job post or version not found

---

#### Update Job Post
```
PUT /api/v1/jobpost/{job_id}
```

**Description:** Update a job post. Creates a new version. Owner and Admin only.

**Authentication:** Required (Recruiter/Admin)

**Path Parameters:**
- `job_id` (required): UUID of the job post

**Request Body:**
```json
{
  "job_title": "Senior Backend Engineer (Updated)",
  "min_experience": 6,
  "max_experience": 12,
  "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"]
}
```

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_title": "Senior Backend Engineer (Updated)",
  "description": "We are looking for a senior backend engineer...",
  "min_experience": 6,
  "max_experience": 12,
  "min_educational_qualifications": "Bachelor's in CS",
  "job_type": "Full-time",
  "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
  "preferred_skills": ["Kubernetes", "AWS"],
  "location_preference": "Remote",
  "status": "active",
  "no_of_candidates_required": 3,
  "created_by": "550e8400-e29b-41d4-a716-446655440001",
  "version": 2
}
```

**Error Responses:**
- `404 Not Found`: Job post not found
- `403 Forbidden`: Insufficient permissions
- `400 Bad Request`: Invalid input

---

#### Close Job Post
```
PUT /api/v1/jobpost/{job_id}/close
```

**Description:** Mark a job post as closed. Owner and Admin only.

**Authentication:** Required (Recruiter/Admin)

**Path Parameters:**
- `job_id` (required): UUID of the job post

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "Closed"
}
```

**Error Responses:**
- `404 Not Found`: Job post not found
- `403 Forbidden`: Insufficient permissions
- `400 Bad Request`: Job already closed

---

#### Delete All Job Posts
```
DELETE /api/v1/jobpost
```

**Description:** Delete all job posts from the system. Admin only.

**Authentication:** Required (Admin)

**Response:** `204 No Content`

---

### Candidate Shortlist Endpoints

#### Get Shortlist for Job
```
GET /api/v1/shortlist/{job_id}
```

**Description:** Retrieve shortlisted candidates for a job (limited to required count).

**Authentication:** Required

**Path Parameters:**
- `job_id` (required): UUID of the job post

**Query Parameters:**
- `version` (optional): Specific job version (defaults to latest)

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "shortlist": [
    {
      "candidate_id": "550e8400-e29b-41d4-a716-446655440100",
      "candidate_name": "Alice Johnson",
      "candidate_email": "alice@example.com",
      "recruiter_notes": "Great technical background"
    }
  ],
  "total_candidates": 3
}
```

---

#### Get All Shortlisted Candidates for Job Version
```
GET /api/v1/shortlist/{job_id}/all/version/{version}
```

**Description:** Retrieve all shortlisted candidates for a specific job version.

**Authentication:** Required

**Path Parameters:**
- `job_id` (required): UUID of the job post
- `version` (required): Job version number

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "version": 1,
  "shortlist": [
    {
      "candidate_id": "550e8400-e29b-41d4-a716-446655440100",
      "candidate_name": "Alice Johnson",
      "candidate_email": "alice@example.com",
      "recruiter_notes": "Great technical background"
    },
    {
      "candidate_id": "550e8400-e29b-41d4-a716-446655440101",
      "candidate_name": "Bob Smith",
      "candidate_email": "bob@example.com",
      "recruiter_notes": "Strong system design skills"
    }
  ],
  "total_candidates": 2
}
```

---

#### Get Shortlisted Candidates for Job Version (Limited)
```
GET /api/v1/shortlist/{job_id}/version/{version}
```

**Description:** Retrieve shortlisted candidates for a specific job version (limited to required count).

**Authentication:** Required

**Path Parameters:**
- `job_id` (required): UUID of the job post
- `version` (required): Job version number

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "version": 1,
  "shortlist": [
    {
      "candidate_id": "550e8400-e29b-41d4-a716-446655440100",
      "candidate_name": "Alice Johnson",
      "candidate_email": "alice@example.com",
      "recruiter_notes": "Great technical background"
    }
  ],
  "total_candidates": 3
}
```

---

#### Get Shortlisted Candidate Details
```
GET /api/v1/shortlist/{job_id}/{candidate_id}
```

**Description:** Retrieve detailed information for a shortlisted candidate.

**Authentication:** Required

**Path Parameters:**
- `job_id` (required): UUID of the job post
- `candidate_id` (required): UUID of the candidate

**Response:** `200 OK`
```json
{
  "candidate_id": "550e8400-e29b-41d4-a716-446655440100",
  "candidate_name": "Alice Johnson",
  "candidate_email": "alice@example.com",
  "title": "Senior Software Engineer",
  "location": "San Francisco, CA",
  "hard_skills": ["Python", "FastAPI", "PostgreSQL"],
  "soft_skills": ["Leadership", "Communication"],
  "completion_score": 95,
  "skill_match_score": 88,
  "recency_score": 92,
  "rule_based_score": 85,
  "aggregation_score": 90,
  "ai_score": 87,
  "confidence_score": 0.92,
  "contact_linkedin_url": "https://linkedin.com/in/alice-johnson"
}
```

---

#### Update Shortlisted Candidate Notes
```
PUT /api/v1/shortlist/{job_id}/{candidate_id}
```

**Description:** Add or update recruiter notes for a shortlisted candidate.

**Authentication:** Required (Recruiter)

**Path Parameters:**
- `job_id` (required): UUID of the job post
- `candidate_id` (required): UUID of the candidate

**Request Body:**
```json
{
  "recruiter_notes": "Excellent fit for the role. Schedule first round interview."
}
```

**Response:** `200 OK`
```json
{
  "candidate_id": "550e8400-e29b-41d4-a716-446655440100",
  "recruiter_notes": "Excellent fit for the role. Schedule first round interview."
}
```

**Error Responses:**
- `404 Not Found`: Job post or candidate not found
- `400 Bad Request`: Invalid input

---

### Sourced Candidates Endpoints

#### List All Sourced Candidates
```
GET /api/v1/sourced-candidates
```

**Description:** Retrieve all sourced candidates from the system.

**Authentication:** Required

**Query Parameters:**
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
[
  {
    "candidate_id": "550e8400-e29b-41d4-a716-446655440100",
    "candidate_name": "Alice Johnson",
    "candidate_email": "alice@example.com",
    "title": "Senior Software Engineer",
    "location": "San Francisco, CA",
    "sourced_from": "LinkedIn",
    "created_at": "2024-03-19T10:30:00Z"
  }
]
```

---

#### Get Sourced Candidate by ID
```
GET /api/v1/sourced-candidates/{candidate_id}
```

**Description:** Retrieve details for a specific sourced candidate.

**Authentication:** Required

**Path Parameters:**
- `candidate_id` (required): ID of the candidate

**Response:** `200 OK`
```json
{
  "candidate_id": "550e8400-e29b-41d4-a716-446655440100",
  "candidate_name": "Alice Johnson",
  "candidate_email": "alice@example.com",
  "title": "Senior Software Engineer",
  "location": "San Francisco, CA",
  "skills": ["Python", "FastAPI", "PostgreSQL"],
  "experience_years": 8,
  "sourced_from": "LinkedIn",
  "source_run_id": "550e8400-e29b-41d4-a716-446655440200",
  "created_at": "2024-03-19T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Candidate not found

---

#### Get Sourced Candidates by Source Run
```
GET /api/v1/sourced-candidates/by-source-run/{source_run_id}
```

**Description:** Retrieve all candidates sourced in a specific source run.

**Authentication:** Required

**Path Parameters:**
- `source_run_id` (required): ID of the source run

**Response:** `200 OK`
```json
[
  {
    "candidate_id": "550e8400-e29b-41d4-a716-446655440100",
    "candidate_name": "Alice Johnson",
    "title": "Senior Software Engineer",
    "location": "San Francisco, CA",
    "sourced_from": "LinkedIn"
  }
]
```

**Error Responses:**
- `400 Bad Request`: Invalid source run ID

---

#### Create Sourced Candidate
```
POST /api/v1/sourced-candidates
```

**Description:** Add a new sourced candidate to the database.

**Authentication:** Required

**Request Body:**
```json
{
  "candidate_name": "Charlie Davis",
  "candidate_email": "charlie@example.com",
  "title": "Backend Engineer",
  "location": "Austin, TX",
  "skills": ["Java", "Spring Boot", "MySQL"],
  "experience_years": 6,
  "source_run_id": "550e8400-e29b-41d4-a716-446655440200"
}
```

**Response:** `201 Created`
```json
{
  "candidate_id": "550e8400-e29b-41d4-a716-446655440102",
  "candidate_name": "Charlie Davis",
  "candidate_email": "charlie@example.com",
  "created_at": "2024-03-19T10:45:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input

---

#### Delete Sourced Candidate
```
DELETE /api/v1/sourced-candidates/{candidate_id}
```

**Description:** Remove a sourced candidate from the database.

**Authentication:** Required

**Path Parameters:**
- `candidate_id` (required): ID of the candidate

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found`: Candidate not found

---

### Sourcing Configuration Endpoints

#### Create Sourcing Configuration
```
POST /api/v1/admin/sourcing-config
```

**Description:** Create a new sourcing configuration for the organization. Admin only.

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "search_skills": ["Python", "FastAPI", "PostgreSQL"],
  "search_location": "United States",
  "search_salary_range": "120000-180000",
  "search_experience_level": "senior"
}
```

**Response:** `201 Created`
```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440300",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "search_skills": ["Python", "FastAPI", "PostgreSQL"],
  "search_location": "United States",
  "is_active": true,
  "created_at": "2024-03-19T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input

---

#### Get Active Sourcing Configuration
```
GET /api/v1/admin/sourcing-config
```

**Description:** Retrieve the active sourcing configuration for the organization. Admin only.

**Authentication:** Required (Admin)

**Response:** `200 OK`
```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440300",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "search_skills": ["Python", "FastAPI", "PostgreSQL"],
  "search_location": "United States",
  "is_active": true,
  "created_at": "2024-03-19T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: No active configuration found

---

#### Get Sourcing Configuration by ID
```
GET /api/v1/admin/sourcing-config/{config_id}
```

**Description:** Retrieve a specific sourcing configuration by ID. Admin only.

**Authentication:** Required (Admin)

**Path Parameters:**
- `config_id` (required): UUID of the configuration

**Response:** `200 OK`
```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440300",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "search_skills": ["Python", "FastAPI", "PostgreSQL"],
  "search_location": "United States",
  "is_active": true,
  "created_at": "2024-03-19T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid config_id format
- `400 Bad Request`: Configuration not found

---

#### Update Sourcing Configuration
```
PUT /api/v1/admin/sourcing-config/{config_id}
```

**Description:** Update an existing sourcing configuration. Admin only.

**Authentication:** Required (Admin)

**Path Parameters:**
- `config_id` (required): UUID of the configuration

**Request Body:**
```json
{
  "search_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
  "search_location": "North America",
  "search_salary_range": "130000-200000"
}
```

**Response:** `200 OK`
```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440300",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "search_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
  "search_location": "North America",
  "is_active": true,
  "updated_at": "2024-03-19T11:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input or configuration not found

---

#### Deactivate Sourcing Configuration
```
DELETE /api/v1/admin/sourcing-config
```

**Description:** Deactivate the active sourcing configuration for the organization. Admin only.

**Authentication:** Required (Admin)

**Response:** `204 No Content`

**Error Responses:**
- `400 Bad Request`: No active configuration to deactivate

---

### Role & Permissions Endpoints

#### List All Roles
```
GET /api/v1/role-permission/roles
```

**Description:** Retrieve all available roles in the system.

**Authentication:** Required

**Response:** `200 OK`
```json
[
  {
    "role_id": 1,
    "role": "Admin",
    "created_at": "2024-03-19T10:30:00Z"
  },
  {
    "role_id": 2,
    "role": "Recruiter",
    "created_at": "2024-03-19T10:30:00Z"
  },
  {
    "role_id": 3,
    "role": "View Only",
    "created_at": "2024-03-19T10:30:00Z"
  }
]
```

---

#### Get Role by ID
```
GET /api/v1/role-permission/roles/{role_id}
```

**Description:** Retrieve role details by ID.

**Authentication:** Required

**Path Parameters:**
- `role_id` (required): ID of the role

**Response:** `200 OK`
```json
{
  "role_id": 2,
  "role": "Recruiter",
  "created_at": "2024-03-19T10:30:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Role not found

---

#### Create Role
```
POST /api/v1/role-permission/roles
```

**Description:** Create a new role. Admin only.

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "role": "Team Lead"
}
```

**Response:** `201 Created`
```json
{
  "role_id": 4,
  "role": "Team Lead",
  "created_at": "2024-03-19T10:45:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Role already exists or invalid input

---

#### Delete Role
```
DELETE /api/v1/role-permission/roles/{role_id}
```

**Description:** Delete a role from the system. Admin only.

**Authentication:** Required (Admin)

**Path Parameters:**
- `role_id` (required): ID of the role

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found`: Role not found

---

#### List All Permissions
```
GET /api/v1/role-permission/permissions
```

**Description:** Retrieve all available permissions in the system.

**Authentication:** Required

**Response:** `200 OK`
```json
[
  {
    "permission_id": 1,
    "entity_name": "Job Post",
    "action": "create"
  },
  {
    "permission_id": 2,
    "entity_name": "Job Post",
    "action": "edit"
  }
]
```

---

#### Get Permission by ID
```
GET /api/v1/role-permission/permissions/{permission_id}
```

**Description:** Retrieve permission details by ID.

**Authentication:** Required

**Path Parameters:**
- `permission_id` (required): ID of the permission

**Response:** `200 OK`
```json
{
  "permission_id": 1,
  "entity_name": "Job Post",
  "action": "create"
}
```

**Error Responses:**
- `404 Not Found`: Permission not found

---

#### Create Permission
```
POST /api/v1/role-permission/permissions
```

**Description:** Create a new permission. Admin only.

**Authentication:** Required (Admin)

**Request Body:**
```json
{
  "entity_name": "Candidate",
  "action": "shortlist"
}
```

**Response:** `201 Created`
```json
{
  "permission_id": 5,
  "entity_name": "Candidate",
  "action": "shortlist"
}
```

---

### Source Runs Endpoints

#### Create Source Run Record
```
POST /api/v1/source-runs
```

**Description:** Create a new source run record in the database.

**Authentication:** Required

**Request Body:**
```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440300",
  "status": "pending",
  "total_candidates_found": 0
}
```

**Response:** `200 OK`
```json
{
  "message": "Source run record created",
  "config": {
    "config_id": "550e8400-e29b-41d4-a716-446655440300",
    "status": "pending"
  }
}
```

---

#### Get All Source Run Records
```
GET /api/v1/source-runs
```

**Description:** Fetch all source run records from the database.

**Authentication:** Required

**Response:** `200 OK`
```json
[
  {
    "source_run_id": "550e8400-e29b-41d4-a716-446655440200",
    "config_id": "550e8400-e29b-41d4-a716-446655440300",
    "status": "completed",
    "total_candidates_found": 150,
    "created_at": "2024-03-19T10:30:00Z"
  }
]
```

---

#### Get Source Run by ID
```
GET /api/v1/source-runs/{source_run_id}
```

**Description:** Fetch a single source run record by its ID.

**Authentication:** Required

**Path Parameters:**
- `source_run_id` (required): UUID of the source run

**Response:** `200 OK`
```json
{
  "source_run_id": "550e8400-e29b-41d4-a716-446655440200",
  "config_id": "550e8400-e29b-41d4-a716-446655440300",
  "status": "completed",
  "total_candidates_found": 150,
  "created_at": "2024-03-19T10:30:00Z"
}
```

---

#### Delete Source Run
```
DELETE /api/v1/source-runs/{source_run_id}
```

**Description:** Delete a source run record by its ID.

**Authentication:** Required

**Path Parameters:**
- `source_run_id` (required): UUID of the source run

**Response:** `200 OK`
```json
{
  "message": "Source run 550e8400-e29b-41d4-a716-446655440200 deleted"
}
```

**Error Responses:**
- `500 Internal Server Error`: Deletion failed

---

## Error Handling

All error responses follow a consistent JSON format:

```json
{
  "detail": "Descriptive error message"
}
```

### Common Error Scenarios

#### Invalid Credentials
```
Status: 401 Unauthorized
{
  "detail": "Invalid credentials"
}
```

#### Resource Not Found
```
Status: 404 Not Found
{
  "detail": "[Resource] not found"
}
```

#### Validation Error
```
Status: 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

#### Permission Denied
```
Status: 403 Forbidden
{
  "detail": "Insufficient permissions"
}
```

#### Server Error
```
Status: 500 Internal Server Error
{
  "detail": "An internal server error occurred"
}
```

## Rate Limiting

Rate limiting is implemented on a per-user basis to prevent abuse:

- **Default**: 1000 requests per hour per authenticated user
- **Burst**: Maximum 50 requests per minute

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Total requests allowed per hour
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

When rate limited:
```
Status: 429 Too Many Requests
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

## Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Successful deletion or update |
| 400 | Bad Request - Invalid input or request format |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource does not exist |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

## Pagination

List endpoints support pagination using query parameters:

```
GET /api/v1/users?limit=20&offset=40
```

**Query Parameters:**
- `limit`: Number of results per page (default: 50, max: 100)
- `offset`: Number of items to skip (default: 0)

**Response Headers:**
- `X-Total-Count`: Total number of items available

## Filtering

Many list endpoints support filtering:

```
GET /api/v1/jobpost?status=active&location=remote&created_by=550e8400-e29b-41d4-a716-446655440001
```

Refer to individual endpoint documentation for available filter parameters.

## Sorting

Some endpoints support sorting via query parameters:

```
GET /api/v1/jobpost?sort_by=created_at&sort_order=desc
```

## API Best Practices

1. **Always use HTTPS** in production
2. **Keep tokens secure** - Store refresh tokens securely (httpOnly cookies)
3. **Implement retry logic** with exponential backoff for failed requests
4. **Handle rate limiting** gracefully
5. **Validate input** on client side before submission
6. **Use appropriate HTTP methods** (GET, POST, PUT, DELETE)
7. **Include descriptive error handling** in your client application
8. **Monitor API usage** to optimize integration
9. **Test endpoints** in staging environment before production use
10. **Keep user agents** consistent for proper tracking and support
