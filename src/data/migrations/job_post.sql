
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE DATABASE "TalentFinder";

CREATE TABLE roles (
    role_id     SERIAL PRIMARY KEY,
    role        VARCHAR NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);


CREATE TABLE permissions (
    permission_id   SERIAL PRIMARY KEY,
    entity_name     VARCHAR NOT NULL,
    action          VARCHAR NOT NULL
);

CREATE TABLE role_permission_map (
    role_id         INT NOT NULL REFERENCES roles(role_id),
    permission_id   INT NOT NULL REFERENCES permissions(permission_id),
    PRIMARY KEY (role_id, permission_id)
);


CREATE TABLE organizations (
    org_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_name    VARCHAR NOT NULL,
    org_logo    VARCHAR,
    created_at  TIMESTAMP DEFAULT NOW()
);


CREATE TABLE users (
    user_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               VARCHAR NOT NULL UNIQUE,
    hashed_password     VARCHAR NOT NULL,
    role_id             INT REFERENCES roles(role_id),
    name                VARCHAR,
    org_id              UUID REFERENCES organizations(org_id),
    created_at          TIMESTAMP,
    updated_at          TIMESTAMP
);



CREATE TABLE refresh_tokens (
    jti         UUID PRIMARY KEY,
    session_id  UUID NOT NULL,
    user_id     UUID REFERENCES users(user_id),
    is_rotated  BOOLEAN DEFAULT FALSE,
    parent_jti  UUID,
    rotated_at  TIMESTAMP,
    expires_at  TIMESTAMP NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);



CREATE TABLE revoked_tokens (
    jti         UUID PRIMARY KEY REFERENCES refresh_tokens(jti),
    revoked_at  TIMESTAMP DEFAULT NOW(),
    expires_at  TIMESTAMP NOT NULL
);



CREATE TABLE job_posts (
    job_id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_title                       VARCHAR NOT NULL,
    description                     TEXT,
    min_experience                  INT,
    max_experience                  INT,
    min_educational_qualifications  VARCHAR,
    job_type                        VARCHAR,
    required_skills                 VARCHAR[],
    preferred_skills                VARCHAR[],
    location_preference             VARCHAR,
    status                          VARCHAR NOT NULL,
    no_of_candidates_required       INT,
    created_by                      UUID REFERENCES users(user_id),
    version    
	INT DEFAULT 1,
    created_on                      TIMESTAMP DEFAULT NOW(),
    updated_on                      TIMESTAMP,
    updated_by                      UUID REFERENCES users(user_id)
);


CREATE TABLE jd_enrichments (
    enrichment_id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enrichment_run_id               UUID NOT NULL,
    job_id                          UUID REFERENCES job_posts(job_id),
    job_title                       VARCHAR,
    description                     TEXT,
    min_experience                  INT,
    max_experience                  INT,
    min_educational_qualifications  VARCHAR,
    required_skills                 VARCHAR[],
    preferred_skills                VARCHAR[],
    location_preference             VARCHAR,
    status                          VARCHAR
);


CREATE TABLE source_platforms (
    platform_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR NOT NULL,
    base_url            VARCHAR NOT NULL,
    supported_filters   VARCHAR[],
    last_fetch_at       TIMESTAMP,
    status              VARCHAR NOT NULL
);

CREATE TABLE source_runs (
    source_run_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform_id                 UUID REFERENCES source_platforms(platform_id),
    status                      VARCHAR NOT NULL,
    number_of_resume_fetched    INT DEFAULT 0,
    job_id                      UUID REFERENCES job_posts(job_id),
    run_at                      TIMESTAMP DEFAULT NOW()
);


CREATE TABLE job_candidate_shortlist (
    job_candidate_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id              UUID NOT NULL REFERENCES job_posts(job_id),
    candidate_id        UUID NOT NULL,
    recruiter_notes     VARCHAR,
    reviewed_by         UUID REFERENCES users(user_id)
);



CREATE INDEX idx_users_email           ON users(email);
CREATE INDEX idx_users_org_id          ON users(org_id);
CREATE INDEX idx_refresh_tokens_user   ON refresh_tokens(user_id);
CREATE INDEX idx_job_posts_status      ON job_posts(status);
CREATE INDEX idx_job_posts_created_by  ON job_posts(created_by);
CREATE INDEX idx_source_runs_job_id    ON source_runs(job_id);
CREATE INDEX idx_source_runs_platform  ON source_runs(platform_id);
CREATE INDEX idx_jd_enrichments_job    ON jd_enrichments(job_id);
CREATE INDEX idx_shortlist_job_id      ON job_candidate_shortlist(job_id);
CREATE INDEX idx_shortlist_candidate   ON job_candidate_shortlist(candidate_id);