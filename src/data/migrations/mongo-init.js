// MongoDB initialization script for TalentFinder
// This script creates basic collections and indexes
// Candidate data is seeded via seed_resume.py (Python script)

// Connect to the talentfinder database
db = db.getSiblingDB('talentfinder');

// Create collections
db.createCollection('sourced_candidates');
db.createCollection('candidates');

print("✓ Created collections: sourced_candidates, candidates, shortlists, source_runs");

// Create sparse indexes for sourced_candidates collection (sparse allows multiple nulls)
db.sourced_candidates.createIndex({ candidate_id: 1 }, { unique: true, sparse: true });
db.sourced_candidates.createIndex({ platform_id: 1 });
db.sourced_candidates.createIndex({ source_run_id: 1 });
db.sourced_candidates.createIndex({ sourced_at: 1 });
db.sourced_candidates.createIndex({ job_id: 1 });

print("✓ Created indexes for sourced_candidates");

// Create indexes for other collections
db.candidates.createIndex({ email: 1 });
db.candidates.createIndex({ source_run_id: 1 });
db.shortlists.createIndex({ job_id: 1 });
db.shortlists.createIndex({ candidate_id: 1 });
db.source_runs.createIndex({ job_id: 1 });

print("✓ Created indexes for all collections");
print("═══════════════════════════════════════");
print("MongoDB initialization completed!");
print("Note: Run 'python src/utils/seed_resume.py' to seed candidate data");
