import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def seed_database_from_sql(engine) -> None:
    """
    Seed the database with initial data (roles, permissions, users).
    Executes hardcoded SQL statements in Python.
    """
    try:
        print("=== Starting database seed with hardcoded SQL ===")
        
        # Define SQL statements directly in Python
        statements = [
            # Insert roles
            "INSERT INTO roles (role, created_at) VALUES ('Admin', NOW()) ON CONFLICT DO NOTHING;",
            "INSERT INTO roles (role, created_at) VALUES ('Recruiter', NOW()) ON CONFLICT DO NOTHING;",
            
            # Insert permissions
            "INSERT INTO permissions (entity_name, action) VALUES ('job_post', 'create') ON CONFLICT DO NOTHING;",
            "INSERT INTO permissions (entity_name, action) VALUES ('job_post', 'read') ON CONFLICT DO NOTHING;",
            "INSERT INTO permissions (entity_name, action) VALUES ('job_post', 'update') ON CONFLICT DO NOTHING;",
            "INSERT INTO permissions (entity_name, action) VALUES ('job_post', 'delete') ON CONFLICT DO NOTHING;",
            "INSERT INTO permissions (entity_name, action) VALUES ('user', 'create') ON CONFLICT DO NOTHING;",
            "INSERT INTO permissions (entity_name, action) VALUES ('user', 'read') ON CONFLICT DO NOTHING;",
            "INSERT INTO permissions (entity_name, action) VALUES ('user', 'update') ON CONFLICT DO NOTHING;",
            "INSERT INTO permissions (entity_name, action) VALUES ('user', 'delete') ON CONFLICT DO NOTHING;",
            
            # Insert organization
            "INSERT INTO organizations (org_id, org_name, org_logo, created_at) VALUES ('12345678-1234-1234-1234-123456789012', 'TalentFinder Inc.', 'https://example.com/logo.png', NOW()) ON CONFLICT DO NOTHING;",
            
            # Insert test admin user: admin@talentfinder.com / User@123
            """INSERT INTO users (user_id, email, hashed_password, role_id, name, org_id, created_at) 
               VALUES ('2fa85f64-5717-4562-b3fc-2c963f66afa5', 'admin@talentfinder.com', 
                       '$argon2id$v=19$m=65536,t=3,p=4$g3DOec95L+Uco1SKEYLQmg$Jite4qjtnxJLgcbfyXjolSgu/T91dwwqnlBZVjMCyDs',
                       (SELECT role_id FROM roles WHERE role = 'Admin' LIMIT 1), 'Admin User', 
                       '12345678-1234-1234-1234-123456789012', NOW())
               ON CONFLICT (email) DO NOTHING;""",
            
            # Insert test recruiter user: recruiter@talentfinder.com / User@123
            """INSERT INTO users (user_id, email, hashed_password, role_id, name, org_id, created_at)
               VALUES ('3fa85f64-5717-4562-b3fc-2c963f66afa6', 'recruiter@talentfinder.com',
                       '$argon2id$v=19$m=65536,t=3,p=4$g3DOec95L+Uco1SKEYLQmg$Jite4qjtnxJLgcbfyXjolSgu/T91dwwqnlBZVjMCyDs',
                       (SELECT role_id FROM roles WHERE role = 'Recruiter' LIMIT 1), 'Recruiter User',
                       '12345678-1234-1234-1234-123456789012', NOW())
               ON CONFLICT (email) DO NOTHING;""",
        ]
        
        executed = 0
        failed = 0
        
        # Execute each statement in its own transaction
        for i, statement in enumerate(statements, 1):
            try:
                print(f"  [{i}/{len(statements)}] Executing: {statement[:60]}...")
                async with engine.begin() as connection:
                    await connection.execute(text(statement))
                executed += 1
            except Exception as e:
                print(f"  [{i}/{len(statements)}] Error: {str(e)[:100]}")
                logger.warning(f"Statement {i} failed: {str(e)}")
                failed += 1
                continue
        
        print(f"=== Database seeding completed: {executed} executed, {failed} failed ===")
        logger.info(f"Database seeding completed: {executed} executed, {failed} failed")
        
    except Exception as e:
        print(f"CRITICAL ERROR during database seeding: {e}")
        logger.error(f"Error during database seeding: {e}", exc_info=True)
        raise
