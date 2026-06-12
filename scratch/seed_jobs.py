import os
import psycopg2
from dotenv import load_dotenv

# Load env variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

JOBS = [
    {
        "title": "Junior Backend Engineer (Python/Flask)",
        "company": "Zomato",
        "logo_url": "https://logo.clearbit.com/zomato.com",
        "location": "Gurugram (Hybrid)",
        "job_type": "Job",
        "category": "Backend",
        "experience_level": "Freshers / 0-1 years",
        "salary": "₹8,00,000 - ₹12,00,000 / year",
        "skills": "Python, Flask, REST APIs, SQL",
        "description": "We are looking for a Junior Backend Engineer who is passionate about food delivery logistics and building highly scalable services.\n\nResponsibilities:\n- Develop and maintain REST APIs using Python and Flask.\n- Write clean, optimized SQL queries and design robust database schemas.\n- Integrate Zomato delivery tracking services with internal map microservices.\n- Write unit tests and debug code logic in dev and staging environments.",
        "course_match": "Perfect fit for students completing Phase 2 (Web & Databases) and Flask APIs.",
        "apply_url": "https://zomato.careers/jobs/junior-backend",
        "is_active": True
    },
    {
        "title": "AI Engineering Intern",
        "company": "Razorpay",
        "logo_url": "https://logo.clearbit.com/razorpay.com",
        "location": "Bengaluru",
        "job_type": "Internship",
        "category": "AI / LLM",
        "experience_level": "College Students / Freshers",
        "salary": "₹35,000 / month",
        "skills": "Python, LLMs, Prompt Engineering, Flask",
        "description": "Join our AI research cell at Razorpay to build next-generation payment support automation.\n\nResponsibilities:\n- Assist in developing LLM chatbots powered by Groq and Llama.\n- Benchmark prompts to reduce token usage and improve response accuracy.\n- Set up Flask endpoints to pipe user questions to the AI tutor agents.\n- Help document agent safety rules and testing pipelines.",
        "course_match": "Matches outcomes from Day 91-100 (Advanced AI Systems) and our 7-Day AI Agent course.",
        "apply_url": "https://razorpay.careers/internships/ai-engineer",
        "is_active": True
    },
    {
        "title": "Python Developer (Entry Level)",
        "company": "Paytm",
        "logo_url": "https://logo.clearbit.com/paytm.com",
        "location": "Noida",
        "job_type": "Job",
        "category": "Python",
        "experience_level": "0-2 years experience",
        "salary": "₹6,00,000 - ₹9,00,000 / year",
        "skills": "Python, SQLite, PostgreSQL, OOP",
        "description": "Paytm is seeking an entry-level Python developer to join the finance and reconciliations engineering team.\n\nResponsibilities:\n- Write Python scripts to parse daily transaction CSV files and upload them to PostgreSQL.\n- Implement object-oriented logic to validate customer wallets.\n- Work alongside Senior Engineers to debug database connectivity issues.\n- Write SQL aggregation queries to summarize daily merchant settlements.",
        "course_match": "Matches Phase 1 OOP basics and Phase 2 Database design.",
        "apply_url": "https://paytm.careers/jobs/python-entry",
        "is_active": True
    },
    {
        "title": "Software Engineer Intern",
        "company": "Zoho",
        "logo_url": "https://logo.clearbit.com/zoho.com",
        "location": "Chennai",
        "job_type": "Internship",
        "category": "Python",
        "experience_level": "Freshers",
        "salary": "₹20,000 / month",
        "skills": "Python, NumPy, Pandas, SQL",
        "description": "Zoho is hiring Python interns to join the analytics product division.\n\nResponsibilities:\n- Write scripts using NumPy and Pandas to clean and process customer data sets.\n- Implement data validation routines to check for duplicates and nulls.\n- Assist in visual formatting of dashboards.\n- Query PostgreSQL databases to draw simple product usage metrics.",
        "course_match": "Matches Phase 3 (Data Science) NumPy & Pandas curriculum.",
        "apply_url": "https://zoho.com/careers/internship/analytics",
        "is_active": True
    },
    {
        "title": "Junior Data Analyst",
        "company": "Swiggy",
        "logo_url": "https://logo.clearbit.com/swiggy.com",
        "location": "Bengaluru (On-site)",
        "job_type": "Job",
        "category": "Backend",
        "experience_level": "Freshers / 0-2 years",
        "salary": "₹5,00,000 - ₹8,00,000 / year",
        "skills": "Python, Pandas, Matplotlib, SQL",
        "description": "Swiggy is looking for a Junior Data Analyst to help optimize restaurant dispatch times.\n\nResponsibilities:\n- Query Swiggy order databases to extract daily route metrics.\n- Use Pandas and Matplotlib to analyze driver idle times and create plots.\n- Help build data pipelines that feed predictive dispatch models.\n- Clean dataset logs containing delivery partner geo-coordinates.",
        "course_match": "Perfect fit for students who finished Phase 3 Data Science & Data Visualization.",
        "apply_url": "https://swiggy.careers/jobs/junior-data-analyst",
        "is_active": True
    },
    {
        "title": "AI Agent Developer",
        "company": "InMobi",
        "logo_url": "https://logo.clearbit.com/inmobi.com",
        "location": "Bengaluru",
        "job_type": "Job",
        "category": "AI / LLM",
        "experience_level": "Freshers / 0-2 years",
        "salary": "₹10,00,000 - ₹14,00,000 / year",
        "skills": "Python, AI Agents, Groq, LLMs",
        "description": "InMobi is building autonomous ad-campaign managers. We need a junior engineer to help wire LLM actions.\n\nResponsibilities:\n- Build tool functions (APIs) that AI Agents can invoke to retrieve user demographic profiles.\n- Write agent orchestration scripts using Groq API and Python.\n- Parse unstructured LLM outputs into JSON logs for system tracking.\n- Assist in monitoring agent loop token consumption.",
        "course_match": "Matches Day 94-96 Multi-Agent Systems outcomes.",
        "apply_url": "https://inmobi.com/careers/jobs/ai-agent-dev",
        "is_active": True
    },
    {
        "title": "Junior Machine Learning Engineer",
        "company": "Zepto",
        "logo_url": "https://logo.clearbit.com/zepto.com",
        "location": "Mumbai",
        "job_type": "Job",
        "category": "AI / LLM",
        "experience_level": "1-2 years experience",
        "salary": "₹9,00,000 - ₹13,00,000 / year",
        "skills": "Python, Machine Learning, Scikit-Learn, NumPy",
        "description": "Zepto is hiring junior ML engineers to work on local dark-store demand predictions.\n\nResponsibilities:\n- Train linear regression and classification models using Scikit-Learn.\n- Clean dark store transaction records using NumPy and Pandas.\n- Validate model outcomes against holdout test datasets to check for overfitting.\n- Deploy simple prediction pipelines as python microservices.",
        "course_match": "Matches Phase 4 (Machine Learning) Scikit-Learn predictions.",
        "apply_url": "https://zepto.com/careers/ml-demand",
        "is_active": True
    },
    {
        "title": "Data Science Intern",
        "company": "Flipkart",
        "logo_url": "https://logo.clearbit.com/flipkart.com",
        "location": "Bengaluru",
        "job_type": "Internship",
        "category": "Python",
        "experience_level": "Freshers",
        "salary": "₹30,000 / month",
        "skills": "Python, String Operations, Regex, SQL",
        "description": "Flipkart's Catalog team is seeking an intern to help structure seller description fields.\n\nResponsibilities:\n- Write regular expressions (regex) to extract brand and model info from raw text.\n- Implement Python string manipulation functions to clean catalog formats.\n- Query item properties from MySQL database tables.\n- Prepare Excel reports detailing catalog cleaning efficiency.",
        "course_match": "Matches Phase 1 String operations & Phase 2 SQL.",
        "apply_url": "https://flipkart.careers/internships/catalog-science",
        "is_active": True
    },
    {
        "title": "Deep Learning Intern",
        "company": "Jio",
        "logo_url": "https://logo.clearbit.com/jio.com",
        "location": "Navi Mumbai (Hybrid)",
        "job_type": "Internship",
        "category": "AI / LLM",
        "experience_level": "Freshers / Students",
        "salary": "₹25,000 / month",
        "skills": "Python, Deep Learning, PyTorch, TensorFlow",
        "description": "Jio is seeking interns to assist the Computer Vision team with Aadhaar document KYC validation.\n\nResponsibilities:\n- Prepare dataset sets of cropped document images.\n- Assist in training neural networks using PyTorch/TensorFlow for boundary detection.\n- Document activation functions and loss function scores.\n- Implement data augmentation scripts in Python.",
        "course_match": "Matches Phase 5 (Deep Learning) Artificial Neurons & Image Classifiers.",
        "apply_url": "https://jio.com/careers/internships/deep-learning",
        "is_active": True
    },
    {
        "title": "AI Automation Engineer",
        "company": "Ola",
        "logo_url": "https://logo.clearbit.com/ola.com",
        "location": "Bengaluru",
        "job_type": "Job",
        "category": "AI / LLM",
        "experience_level": "Freshers",
        "salary": "₹7,00,000 - ₹10,00,000 / year",
        "skills": "Python, LLMs, AI Automation, REST APIs",
        "description": "Ola is hiring freshers for the AI Operations team to automate mapping updates.\n\nResponsibilities:\n- Write Python automation scripts that call map APIs to check street addresses.\n- Pipe unstructured driver reports through Llama models to extract coordinates.\n- Build simple backend scripts using Flask.\n- Monitor API rate limits and log error rates.",
        "course_match": "Matches Phase 7 AI Automation Workflows lessons.",
        "apply_url": "https://ola.careers/jobs/operations-ai",
        "is_active": True
    }
]

def seed():
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment.")
        return

    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    # Create table if not exists (in case db.create_all has not run yet)
    print("Ensuring table 'jobs' exists...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        company VARCHAR(200) NOT NULL,
        logo_url VARCHAR(300),
        location VARCHAR(200) NOT NULL,
        job_type VARCHAR(50) NOT NULL DEFAULT 'Job',
        category VARCHAR(100) NOT NULL DEFAULT 'Python',
        experience_level VARCHAR(100) NOT NULL DEFAULT 'Freshers',
        salary VARCHAR(100),
        skills VARCHAR(300) NOT NULL,
        description TEXT NOT NULL,
        course_match VARCHAR(300),
        apply_url VARCHAR(500) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT TIMEZONE('utc', NOW())
    );
    """)

    # Check if jobs exist
    cursor.execute("SELECT COUNT(*) FROM jobs;")
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"Database already contains {count} jobs. Skipping seeding.")
        conn.close()
        return

    print("Inserting 10 curated tech jobs...")
    for j in JOBS:
        cursor.execute("""
            INSERT INTO jobs (title, company, logo_url, location, job_type, category, experience_level, salary, skills, description, course_match, apply_url, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (j["title"], j["company"], j["logo_url"], j["location"], j["job_type"], j["category"], j["experience_level"], j["salary"], j["skills"], j["description"], j["course_match"], j["apply_url"], j["is_active"]))

    print("[SUCCESS] Successfully seeded 10 curated Indian tech jobs into PostgreSQL.")
    conn.close()

if __name__ == "__main__":
    seed()
