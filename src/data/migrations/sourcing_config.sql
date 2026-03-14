CREATE TABLE sourcing_config (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id                UUID NOT NULL REFERENCES organizations(org_id),
    is_active             BOOLEAN DEFAULT true,
    frequency             VARCHAR NOT NULL,
    scheduled_time        TIME NOT NULL,
    scheduled_day         VARCHAR,
    github_pat_encrypted  TEXT NOT NULL,
    search_skills         VARCHAR[],
    search_location       VARCHAR,
    min_repos             INT DEFAULT 3,
    min_followers         INT DEFAULT 0,
    max_profiles          INT DEFAULT 500,
    created_by            UUID NOT NULL REFERENCES users(user_id),
    updated_by            UUID REFERENCES users(user_id),
    created_at            TIMESTAMP DEFAULT NOW(),
    updated_at            TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sourcing_config_org ON sourcing_config(org_id);
CREATE INDEX idx_sourcing_config_active ON sourcing_config(is_active);
