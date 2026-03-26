import asyncio
import logging
import os
import random
from datetime import UTC, date, datetime, timedelta
from urllib.parse import quote_plus
from uuid import UUID, uuid4

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne

logger = logging.getLogger(__name__)

# MongoDB connection from environment or defaults
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "devakirubak")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "Kiruba@1809")
MONGO_DB = os.getenv("MONGO_DB", "talentfinder")

# Build connection URI with authentication - properly escape username and password
MONGO_URI = (
    f"mongodb+srv://{quote_plus(MONGO_USER)}:{quote_plus(MONGO_PASSWORD)}"
    f"@talentfinder-cluster.0omhk3c.mongodb.net/{MONGO_DB}"
)

DB_NAME = MONGO_DB
COLLECTION_NAME = "sourced_candidates"

FIXED_PLATFORM_ID = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
FIXED_SOURCE_RUN_ID = UUID("b2c3d4e5-f6a7-8901-bcde-f12345678901")

NAMES = [
    "Arjun Kumar",
    "Priya Sharma",
    "Vikram Singh",
    "Anjali Patel",
    "Rohan Gupta",
    "Neha Verma",
    "Aditya Nair",
    "Divya Iyer",
    "Sanjay Rao",
    "Sneha Desai",
    "Rahul Menon",
    "Pooja Reddy",
    "Karan Kapoor",
    "Shreya Bansal",
    "Varun Sethi",
    "Ananya Dey",
    "Nikhil Joshi",
    "Deepika Singh",
    "Aryan Malhotra",
    "Riya Bhat",
    "Akshay Kumar",
    "Avni Saxena",
    "Chhavi Verma",
    "Dhruv Pandey",
    "Esha Chopra",
    "Farhan Khan",
    "Gauri Mittal",
    "Harsh Agarwal",
    "Ishita Sinha",
    "Jatin Bhatt",
    "Kavya Nambiar",
    "Laksh Srivastava",
    "Madhav Sharma",
    "Nisha Pillai",
    "Omkar Kulkarni",
    "Pavan Kumar",
    "Quincy Adams",
    "Raj Malhotra",
    "Sakshi Roy",
    "Tarun Verma",
    "Uday Singh",
    "Vanya Kapoor",
    "Waqar Ahmed",
    "Xander Cross",
    "Yash Oberoi",
    "Zara Khan",
    "Aisha Iqbal",
    "Bhaskar Rao",
    "Chitra Sinha",
    "Diya Saxena",
    "Emir Hassan",
    "Fiona Kelly",
    "Gaurav Bhatnagar",
    "Hana Patel",
    "Ian Thompson",
    "Jaya Sharma",
    "Kamya Nair",
    "Liam Murphy",
    "Meera Gupta",
    "Nirav Joshi",
    "Ojas Verma",
    "Prithvi Singh",
    "Quinn Blake",
    "Ria Bhat",
    "Sasha Williams",
    "Teja Rao",
    "Uma Pillai",
    "Vikram Reddy",
    "Willa Chen",
    "Yara Ahmed",
    "Zain Khan",
    "Aarushi Malhotra",
    "Bhavesh Saxena",
    "Chandu Sinha",
    "Dhriti Kapoor",
    "Esther James",
    "Farida Khan",
    "Gavin Morris",
    "Hera Patel",
    "Iris Kumar",
    "Jasper White",
    "Kanika Roy",
    "Leo Thompson",
    "Manya Verma",
    "Neeraj Gupta",
    "Orion Black",
    "Priyanka Singh",
    "Quincy Davis",
    "Reyansh Sharma",
    "Simrat Kaur",
    "Tushar Nair",
    "Urvi Bhatnagar",
    "Vansh Kapoor",
    "Winona Roberts",
    "Xenia Cross",
    "Yuki Tanaka",
    "Zoe Mitchell",
]

TITLES = [
    "Software Engineer",
    "Senior Software Engineer",
    "Staff Engineer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "DevOps Engineer",
    "Data Engineer",
    "ML Engineer",
    "Platform Engineer",
    "Site Reliability Engineer",
    "Cloud Architect",
    "Solutions Architect",
    "Engineering Manager",
    "Tech Lead",
    "Principal Engineer",
]

HARD_SKILLS_POOL = [
    "Python",
    "Go",
    "Rust",
    "Java",
    "TypeScript",
    "JavaScript",
    "C++",
    "Kotlin",
    "PostgreSQL",
    "MongoDB",
    "Redis",
    "Elasticsearch",
    "Cassandra",
    "DynamoDB",
    "Kubernetes",
    "Docker",
    "Terraform",
    "Ansible",
    "Helm",
    "ArgoCD",
    "AWS",
    "GCP",
    "Azure",
    "FastAPI",
    "Django",
    "Spring Boot",
    "NestJS",
    "React",
    "Vue",
    "GraphQL",
    "gRPC",
    "Kafka",
    "RabbitMQ",
    "Airflow",
    "Spark",
    "dbt",
    "Flink",
    "PyTorch",
    "TensorFlow",
    "scikit-learn",
    "Prometheus",
    "Grafana",
    "Datadog",
    "OpenTelemetry",
    "Nginx",
]

SOFT_SKILLS_POOL = [
    "Communication",
    "Problem Solving",
    "Team Collaboration",
    "Adaptability",
    "Critical Thinking",
    "Mentorship",
    "Time Management",
    "Leadership",
    "Conflict Resolution",
    "Stakeholder Management",
    "Agile",
    "Scrum",
]

LANGUAGES_POOL = [
    "English",
    "Tamil",
    "Hindi",
    "German",
    "French",
    "Spanish",
    "Mandarin",
    "Japanese",
]

COMPANIES = [
    "Google",
    "Meta",
    "Amazon",
    "Microsoft",
    "Apple",
    "Netflix",
    "Uber",
    "Airbnb",
    "Stripe",
    "Shopify",
    "Atlassian",
    "Twilio",
    "Datadog",
    "HashiCorp",
    "Confluent",
    "Palantir",
    "Snowflake",
    "Databricks",
    "Figma",
    "Notion",
    "Linear",
    "Vercel",
    "PlanetScale",
    "Supabase",
    "Weaviate",
    "Pinecone",
    "Anthropic",
    "OpenAI",
    "Cohere",
    "Mistral AI",
    "Sarvam AI",
    "Zepto",
    "Swiggy",
    "Razorpay",
    "CRED",
]

JOB_ROLES = [
    "Software Engineer",
    "Senior SWE",
    "Staff SWE",
    "Backend Engineer",
    "Frontend Engineer",
    "DevOps Engineer",
    "Data Engineer",
    "ML Engineer",
    "Platform Engineer",
    "SRE",
    "Cloud Engineer",
    "Tech Lead",
]

JOB_TYPES = ["full-time", "contract", "part-time", "internship"]

DEGREES = ["B.Tech", "M.Tech", "B.E", "M.E", "B.Sc", "M.Sc", "MBA", "Ph.D"]

COURSES = [
    "Computer Science",
    "Information Technology",
    "Electronics & Communication",
    "Electrical Engineering",
    "Data Science",
    "Artificial Intelligence",
    "Software Engineering",
    "Cybersecurity",
    "Mathematics",
    "Physics",
]

CERTIFICATIONS = [
    ("AWS Certified Solutions Architect", ["AWS", "Cloud", "IAM", "EC2", "S3"]),
    (
        "Google Cloud Professional Data Engineer",
        ["GCP", "BigQuery", "Dataflow", "Pub/Sub"],
    ),
    ("Certified Kubernetes Administrator", ["Kubernetes", "Docker", "Helm", "etcd"]),
    ("HashiCorp Certified Terraform Associate", ["Terraform", "HCL", "AWS", "Azure"]),
    ("MongoDB Certified Developer", ["MongoDB", "Aggregation", "Atlas"]),
    ("AWS Certified Developer Associate", ["AWS", "Lambda", "DynamoDB", "API Gateway"]),
    ("Certified Scrum Master", ["Agile", "Scrum", "Jira"]),
    ("GCP Professional Cloud Architect", ["GCP", "GKE", "Cloud Run", "VPC"]),
    ("Azure Solutions Architect Expert", ["Azure", "ARM", "AKS", "CosmosDB"]),
    ("Databricks Certified Associate Developer", ["Spark", "Delta Lake", "MLflow"]),
]

LOCATIONS = [
    "Bangalore, India",
    "Chennai, India",
    "Hyderabad, India",
    "Mumbai, India",
    "Pune, India",
    "Delhi, India",
    "San Francisco, USA",
    "New York, USA",
    "Seattle, USA",
    "Austin, USA",
    "Berlin, Germany",
    "London, UK",
    "Singapore",
    "Toronto, Canada",
    "Sydney, Australia",
]

PROJECT_TITLES = [
    "Real-time Analytics Pipeline",
    "Distributed Cache Layer",
    "API Gateway Service",
    "Event-driven Notification System",
    "Multi-tenant SaaS Platform",
    "ML Feature Store",
    "Search Indexing Engine",
    "CI/CD Automation Framework",
    "Data Lakehouse Migration",
    "Zero-downtime Deployment System",
    "GraphQL Federation Gateway",
    "Observability Platform",
    "Auth & RBAC Service",
    "Recommendation Engine",
    "Fraud Detection System",
]

VOLUNTEER_WORKS = [
    "Mentor at GirlScript Summer of Code",
    "Open source contributor to Apache Kafka",
    "Technical reviewer for O'Reilly publications",
    "Speaker at PyCon India",
    "Coach at local coding bootcamp",
    "Organizer at Google Developer Group Chennai",
]

PUBLICATIONS = [
    "Scaling Microservices with Kubernetes — Medium Engineering Blog",
    "Zero-copy Networking in Go — ACM Queue",
    "Vector Databases Explained — Towards Data Science",
    "Building Reliable Data Pipelines — IEEE Conference 2023",
    "LLM Fine-tuning on Domain Data — arXiv preprint",
]


def random_date(start_year: int = 2010, end_year: int = 2023) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def random_datetime(days_back: int = 365) -> datetime:
    return datetime.now(tz=UTC) - timedelta(days=random.randint(0, days_back))


def build_experience(candidate_id: str) -> list[dict]:
    count = random.randint(1, 5)
    experiences = []
    end = date.today()
    for _ in range(count):
        duration_months = random.randint(6, 36)
        start = end - timedelta(days=duration_months * 30)
        experiences.append(
            {
                "experience_id": str(uuid4()),
                "candidate_id": candidate_id,
                "company_name": random.choice(COMPANIES),
                "start_date": start.isoformat(),
                "end_date": end.isoformat() if random.random() > 0.15 else None,
                "technology": random.sample(HARD_SKILLS_POOL, k=random.randint(3, 8)),
                "job_role": random.choice(JOB_ROLES),
                "job_type": random.choice(JOB_TYPES),
            }
        )
        end = start - timedelta(days=random.randint(0, 60))
    return experiences


def build_projects(candidate_id: str) -> list[dict]:
    count = random.randint(1, 4)
    return [
        {
            "project_id": str(uuid4()),
            "candidate_id": candidate_id,
            "title": random.choice(PROJECT_TITLES),
            "description": f"Designed and implemented a "
            f"{random.choice(PROJECT_TITLES).lower()} using "
            f"{', '.join(random.sample(HARD_SKILLS_POOL, 3))}.",
            "technology_used": random.sample(HARD_SKILLS_POOL, k=random.randint(2, 6)),
            "duration": f"{random.randint(1, 12)} months",
        }
        for _ in range(count)
    ]


def build_education(candidate_id: str) -> list[dict]:
    count = random.randint(1, 2)
    return [
        {
            "education_id": str(uuid4()),
            "candidate_id": candidate_id,
            "degree": random.choice(DEGREES),
            "course": random.choice(COURSES),
        }
        for _ in range(count)
    ]


def build_certifications(candidate_id: str) -> list[dict]:
    count = random.randint(0, 3)
    chosen = random.sample(CERTIFICATIONS, k=count)
    return [
        {
            "certification_id": str(uuid4()),
            "candidate_id": candidate_id,
            "certification_name": name,
            "related_technology": techs,
        }
        for name, techs in chosen
    ]


def build_candidate(job_id: str | None = None) -> dict:
    object_id = str(uuid4()).replace("-", "")[:24]
    candidate_id = str(uuid4())
    resume_id = str(uuid4())

    experience = build_experience(object_id)
    projects = build_projects(object_id)
    education = build_education(object_id)
    certifications = build_certifications(object_id)
    candidate_name = random.choice(NAMES)
    candidate_email = f"{candidate_name.lower().replace(' ', '.')}@example.com"

    return {
        "_id": object_id,
        "candidate_id": candidate_id,
        "hash": uuid4().hex,
        "candidate_name": candidate_name,
        "resume_id": resume_id,
        "platform_id": str(FIXED_PLATFORM_ID),
        "sourced_at": random_datetime(180).isoformat(),
        "source_run_id": str(FIXED_SOURCE_RUN_ID),
        "job_id": job_id,
        "updated_on": random_datetime(30).isoformat(),
        "title": random.choice(TITLES),
        "summary": (
            f"Experienced {random.choice(TITLES).lower()} with "
            f"{random.randint(2, 15)}+ years building scalable systems using "
            f"{', '.join(random.sample(HARD_SKILLS_POOL, 3))}. "
            f"Passionate about distributed systems, reliability, and "
            f"developer experience."
        ),
        "hard_skills": random.sample(HARD_SKILLS_POOL, k=random.randint(5, 12)),
        "soft_skills": random.sample(SOFT_SKILLS_POOL, k=random.randint(3, 6)),
        "languages_known": random.sample(LANGUAGES_POOL, k=random.randint(1, 4)),
        "volunteer_works": random.sample(VOLUNTEER_WORKS, k=random.randint(0, 2)),
        "publications": random.sample(PUBLICATIONS, k=random.randint(0, 2)),
        "location": random.choice(LOCATIONS),
        "contact_phone": f"+91{random.randint(6000000000, 9999999999)}",
        "contact_linkedin_url": f"https://linkedin.com/in/candidate-{candidate_id[:8]}",
        "candidate_email": candidate_email,
        "portfolio_url": f"https://github.com/candidate-{candidate_id[:8]}"
        if random.random() > 0.3
        else None,
        "experience": experience,
        "projects": projects,
        "education": education,
        "certifications": certifications,
        "parsed_resume_data": {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "title": random.choice(TITLES),
            "experience": experience,
            "projects": projects,
            "education": education,
            "certifications": certifications,
            "hard_skills": random.sample(HARD_SKILLS_POOL, k=random.randint(5, 12)),
            "soft_skills": random.sample(SOFT_SKILLS_POOL, k=random.randint(3, 6)),
            "summary": (
                f"Experienced {random.choice(TITLES).lower()} with "
                f"{random.randint(2, 15)}+ years building scalable systems using "
                f"{', '.join(random.sample(HARD_SKILLS_POOL, 3))}. "
                f"Passionate about distributed systems, reliability, and "
                f"developer experience."
            ),
        },
    }


async def seed(job_id: str | None = None) -> None:
    try:
        import asyncio

        # Create client with shorter timeout to fail fast if MongoDB is unavailable
        client = AsyncIOMotorClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
        )

        # Test connection with timeout
        try:
            await asyncio.wait_for(client.server_info(), timeout=5)
        except TimeoutError:
            logger.warning("MongoDB connection timeout - skipping resume seeding")
            client.close()
            return
        except Exception as e:
            logger.error(f"MongoDB connection failed - skipping resume seeding: {e}")
            client.close()
            return

        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        if len(await collection.count_documents({})) > 0:
            logger.info(
                f"Collection '{COLLECTION_NAME}' already has data - skipping seeding"
            )
            client.close()
            return

        # If no job_id provided, create generic candidates for any job (testing mode)
        candidates = [build_candidate(job_id) for _ in range(30)]
        operations = [InsertOne(doc) for doc in candidates]

        result = await collection.bulk_write(operations, ordered=False)
        mode = f"job_id={job_id}" if job_id else "GENERIC (available for any job)"
        logger.info(
            f"Inserted {result.inserted_count} candidates into "
            f"'{COLLECTION_NAME}' [{mode}]"
        )

        await collection.create_index("candidate_id", unique=True)
        await collection.create_index("platform_id")
        await collection.create_index("source_run_id")
        await collection.create_index("sourced_at")
        await collection.create_index("job_id")

        logger.info("Indexes created.")
        client.close()
    except Exception as e:
        logger.error(f"Resume seeding error: {e}")


if __name__ == "__main__":
    import sys

    job_id = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(seed(job_id))
