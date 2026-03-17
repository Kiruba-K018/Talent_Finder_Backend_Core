-- Database initialization script
-- Tables will be created in the database specified by POSTGRES_DB

-- Create UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
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
    version                         INT DEFAULT 1,
    created_at                      TIMESTAMP DEFAULT NOW(),
    updated_at                      TIMESTAMP DEFAULT NOW(),
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
CREATE TABLE job_candidate_shortlist (
    job_candidate_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id              UUID NOT NULL REFERENCES job_posts(job_id),
    version             INT NOT NULL DEFAULT 1,
    candidate_id        UUID NOT NULL,
    recruiter_notes     VARCHAR,
    reviewed_by         UUID REFERENCES users(user_id)
);


CREATE TABLE source_platforms (
    platform_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR NOT NULL,
    base_url            VARCHAR NOT NULL,
    supported_filters   VARCHAR[],
    last_fetch_at       TIMESTAMP,
    status              VARCHAR NOT NULL
);
CREATE TABLE sourcing_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    frequency VARCHAR(20) NOT NULL,
    scheduled_time TIME NOT NULL,
    scheduled_day VARCHAR(20),
    search_skills TEXT[] NOT NULL DEFAULT '{}',
    search_location VARCHAR(255) NOT NULL,
    max_profiles INTEGER NOT NULL DEFAULT 10,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_by UUID,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE source_runs (
    source_run_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform_id                 UUID NOT NULL,
    status                      VARCHAR(50) NOT NULL,
    number_of_resume_fetched    INTEGER NOT NULL DEFAULT 0,
    job_id                      UUID NOT NULL,
    created_at                  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMP,
    resume_stats                INTEGER[] DEFAULT '{0,0,0}'
);


CREATE INDEX IF NOT EXISTS idx_sourcing_configs_org_id    ON sourcing_configs (org_id);
CREATE INDEX IF NOT EXISTS idx_sourcing_configs_is_active ON sourcing_configs (is_active);
CREATE INDEX IF NOT EXISTS idx_source_runs_platform ON source_runs (platform_id);
CREATE INDEX IF NOT EXISTS idx_source_runs_status ON source_runs (status);
CREATE INDEX IF NOT EXISTS idx_source_runs_created_at ON source_runs (created_at DESC);


CREATE INDEX idx_users_email           ON users(email);
CREATE INDEX idx_users_org_id          ON users(org_id);
CREATE INDEX idx_refresh_tokens_user   ON refresh_tokens(user_id);
CREATE INDEX idx_job_posts_status      ON job_posts(status);
CREATE INDEX idx_job_posts_created_by  ON job_posts(created_by);
CREATE INDEX idx_jd_enrichments_job    ON jd_enrichments(job_id);
CREATE INDEX idx_shortlist_job_id      ON job_candidate_shortlist(job_id);
CREATE INDEX idx_shortlist_candidate   ON job_candidate_shortlist(candidate_id);
CREATE INDEX idx_sourcing_configs_org ON sourcing_configs(org_id);
CREATE INDEX idx_sourcing_configs_active ON sourcing_configs(is_active);


INSERT INTO roles (role, created_at) VALUES 
('Admin', NOW()),
('Recruiter', NOW());

INSERT INTO permissions (entity_name, action) VALUES
('job_post', 'create'),
('job_post', 'read'),
('job_post', 'update'),
('job_post', 'delete'),
('user', 'create'),
('user', 'read'),
('user', 'update'),
('user', 'delete');


INSERT INTO role_permission_map (role_id, permission_id) VALUES
((SELECT role_id FROM roles WHERE role = 'Admin'), (SELECT permission_id FROM permissions WHERE entity_name = 'job_post' AND action = 'create')),
((SELECT role_id FROM roles WHERE role = 'Admin'), (SELECT permission_id FROM permissions WHERE entity_name = 'job_post' AND action = 'read')),
((SELECT role_id FROM roles WHERE role = 'Admin'), (SELECT permission_id FROM permissions WHERE entity_name = 'job_post' AND action = 'update')),
((SELECT role_id FROM roles WHERE role = 'Admin'), (SELECT permission_id FROM permissions WHERE entity_name = 'job_post' AND action = 'delete')),
((SELECT role_id FROM roles WHERE role = 'Admin'), (SELECT permission_id FROM permissions WHERE entity_name = 'user' AND action = 'create')),
((SELECT role_id FROM roles WHERE role = 'Admin'), (SELECT permission_id FROM permissions WHERE entity_name = 'user' AND action = 'read')),
((SELECT role_id FROM roles WHERE role = 'Admin'), (SELECT permission_id FROM permissions WHERE entity_name = 'user' AND action = 'update')),
((SELECT role_id FROM roles WHERE role = 'Admin'), (SELECT permission_id FROM permissions WHERE entity_name = 'user' AND action = 'delete')),
((SELECT role_id FROM roles WHERE role = 'Recruiter'), (SELECT permission_id FROM permissions WHERE entity_name = 'job_post' AND action = 'create')),
((SELECT role_id FROM roles WHERE role = 'Recruiter'), (SELECT permission_id FROM permissions WHERE entity_name = 'job_post' AND action = 'read')),
((SELECT role_id FROM roles WHERE role = 'Recruiter'), (SELECT permission_id FROM permissions WHERE entity_name = 'job_post' AND action = 'update')),
((SELECT role_id FROM roles WHERE role = 'Recruiter'), (SELECT permission_id FROM permissions WHERE entity_name = 'job_post' AND action = 'delete'));

INSERT INTO organizations (org_name, org_logo, created_at) VALUES ('TalentFinder Inc.', 'https://example.com/logo.png', NOW());

-- Test admin user: admin@talentfinder.com / User@123
-- Test recruiter user: recruiter@talentfinder.com / User@123
INSERT INTO users(user_id, email, hashed_password, role_id, name, org_id, created_at) VALUES 
('2fa85f64-5717-4562-b3fc-2c963f66afa5', 'admin@talentfinder.com', '$argon2id$v=19$m=65536,t=3,p=4$g3DOec95L+Uco1SKEYLQmg$Jite4qjtnxJLgcbfyXjolSgu/T91dwwqnlBZVjMCyDs', (SELECT role_id FROM roles WHERE role = 'Admin'), 'Admin User', (SELECT org_id FROM organizations WHERE org_name = 'TalentFinder Inc.'), NOW()),
('3fa85f64-5717-4562-b3fc-2c963f66afa6', 'recruiter@talentfinder.com', '$argon2id$v=19$m=65536,t=3,p=4$g3DOec95L+Uco1SKEYLQmg$Jite4qjtnxJLgcbfyXjolSgu/T91dwwqnlBZVjMCyDs', (SELECT role_id FROM roles WHERE role = 'Recruiter'), 'Recruiter User', (SELECT org_id FROM organizations WHERE org_name = 'TalentFinder Inc.'), NOW());
