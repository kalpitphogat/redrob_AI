"""
config.py — Central configuration for the Redrob candidate ranking system.

All tunable weights, thresholds, keyword lists, and scoring parameters
are defined here. Derived from careful analysis of the Senior AI Engineer
job description at Redrob AI.
"""

from datetime import date

# ============================================================================
# Scoring dimension weights (must sum to 1.0)
# ============================================================================
WEIGHTS = {
    "title_career": 0.30,       # Title relevance + career trajectory
    "skills_match": 0.25,       # Skill-JD alignment with trust scoring
    "career_description": 0.15, # NLP keywords in career history descriptions
    "experience_fit": 0.15,     # Years-of-experience band fit
    "location": 0.10,           # Geographic proximity to Pune/Noida
    "education": 0.05,          # Degree + institution tier (low weight per JD)
}

# ============================================================================
# Title relevance mapping
# ============================================================================
# Scores from 0.0 to 1.0 based on how well the title matches the JD.
# The JD is for "Senior AI Engineer" on a founding team building
# ranking/retrieval/matching systems.
TITLE_SCORES = {
    # Tier 1: Direct match
    "ai engineer": 1.0,
    "senior ai engineer": 1.0,
    "lead ai engineer": 0.98,
    "staff ai engineer": 0.95,
    "principal ai engineer": 0.93,
    "ml engineer": 0.95,
    "senior ml engineer": 0.97,
    "lead ml engineer": 0.96,
    "machine learning engineer": 0.95,
    "senior machine learning engineer": 0.97,
    "applied ml engineer": 0.95,
    "nlp engineer": 0.92,
    "senior nlp engineer": 0.94,
    "search engineer": 0.93,
    "ranking engineer": 0.95,
    "recommendation engineer": 0.90,
    "ai/ml engineer": 1.0,

    # Tier 2: Strong adjacent
    "data scientist": 0.78,
    "senior data scientist": 0.80,
    "lead data scientist": 0.80,
    "applied scientist": 0.82,
    "research engineer": 0.72,
    "research scientist": 0.68,
    "deep learning engineer": 0.88,
    "ml scientist": 0.75,
    "ai researcher": 0.68,
    "computer vision engineer": 0.55,  # JD says CV without NLP is a concern

    # Tier 3: Adjacent technical
    "software engineer": 0.50,
    "senior software engineer": 0.52,
    "staff software engineer": 0.50,
    "principal software engineer": 0.48,
    "backend engineer": 0.48,
    "senior backend engineer": 0.50,
    "full stack engineer": 0.40,
    "senior full stack engineer": 0.42,
    "data engineer": 0.48,
    "senior data engineer": 0.50,
    "platform engineer": 0.42,
    "infrastructure engineer": 0.38,
    "site reliability engineer": 0.30,
    "sre": 0.30,

    # Tier 4: Weakly relevant
    "data analyst": 0.22,
    "senior data analyst": 0.25,
    "business intelligence": 0.15,
    "devops engineer": 0.20,
    "qa engineer": 0.12,
    "test engineer": 0.10,
    "frontend engineer": 0.12,
    "ios developer": 0.10,
    "android developer": 0.10,
    "product manager": 0.18,
    "technical product manager": 0.22,
    "engineering manager": 0.25,
    "tech lead": 0.35,
    "cto": 0.30,
    "vp engineering": 0.25,
    "project manager": 0.08,
    "business analyst": 0.08,
    "junior ml engineer": 0.55,
    "junior data scientist": 0.45,
    "junior software engineer": 0.30,
    "intern": 0.05,

    # Tier 5: Not relevant
    "marketing manager": 0.02,
    "hr manager": 0.02,
    "operations manager": 0.02,
    "accountant": 0.01,
    "content writer": 0.02,
    "sales executive": 0.01,
    "customer support": 0.01,
    "graphic designer": 0.01,
    "mechanical engineer": 0.03,
    "civil engineer": 0.02,
    "electrical engineer": 0.05,
    "ui designer": 0.03,
    "ux designer": 0.03,
    "ui/ux designer": 0.03,
}

# ============================================================================
# Skills taxonomy
# ============================================================================
# Points awarded per skill category. Within each category, trust-weighted.

MUST_HAVE_SKILLS = {
    # Embeddings & retrieval (JD: "Production experience with embeddings-based retrieval")
    "sentence-transformers", "sentence transformers", "bge", "e5 embeddings",
    "embeddings", "word embeddings", "text embeddings", "embedding models",
    "openai embeddings",
    # Vector DBs (JD: "Production experience with vector databases or hybrid search")
    "pinecone", "weaviate", "qdrant", "milvus", "faiss",
    "elasticsearch", "opensearch", "elastic search",
    "vector database", "vector search", "vector db",
    # Core language
    "python",
    # Ranking/Retrieval/Search (JD: "ranking, retrieval, and matching systems")
    "information retrieval", "ranking systems", "search systems",
    "bm25", "retrieval systems", "re-ranking", "reranking",
    "hybrid search", "semantic search", "dense retrieval",
    "learning to rank", "learning-to-rank",
    # Evaluation (JD: "designing evaluation frameworks for ranking systems")
    "ndcg", "mrr", "mean average precision",
}

STRONG_WANT_SKILLS = {
    # LLM fine-tuning (JD: "LLM fine-tuning experience (LoRA, QLoRA, PEFT)")
    "fine-tuning", "fine-tuning llms", "finetuning", "fine tuning",
    "lora", "qlora", "peft",
    # Learning-to-rank (JD: "learning-to-rank models (XGBoost-based or neural)")
    "xgboost", "lightgbm", "catboost", "gradient boosting",
    # NLP fundamentals
    "nlp", "natural language processing",
    "transformers", "huggingface", "hugging face",
    "bert", "gpt", "t5", "llm", "large language models",
    "spacy", "nltk",
    # Deep learning frameworks
    "pytorch", "tensorflow", "keras", "jax",
    # RAG & LLM systems
    "rag", "retrieval augmented generation",
    "langchain", "llamaindex", "llama index",
    "prompt engineering",
    # ML fundamentals
    "scikit-learn", "sklearn",
    "deep learning", "neural networks",
    "machine learning",
}

NICE_TO_HAVE_SKILLS = {
    # MLOps & Infra (JD: nice-to-have)
    "mlops", "ml ops", "mlflow", "kubeflow", "airflow",
    "docker", "kubernetes", "k8s",
    "fastapi", "flask", "django",
    "aws", "gcp", "azure", "aws sagemaker", "sagemaker",
    # Data engineering adjacent
    "spark", "pyspark", "kafka", "redis",
    "sql", "postgresql", "mongodb", "bigquery", "snowflake",
    "pandas", "numpy", "dask",
    # Model serving
    "bentoml", "triton", "tensorrt", "onnx",
    "model deployment", "model serving",
    # Experiment tracking
    "weights & biases", "wandb", "neptune", "dvc",
    # General engineering
    "git", "ci/cd", "terraform",
    "distributed systems", "microservices",
    "feature engineering", "statistical modeling",
    "a/b testing", "experimentation",
    # Open source
    "open source", "open-source contributions",
}

# Points per category (used in scoring)
SKILL_CATEGORY_POINTS = {
    "must_have": 5.0,
    "strong_want": 3.0,
    "nice_to_have": 1.0,
}

# Skills that are NON-TECHNICAL (used for anti-signal detection)
NON_TECH_SKILLS = {
    "sales", "marketing", "seo", "content writing", "content marketing",
    "accounting", "excel", "powerpoint", "photoshop", "illustrator",
    "figma", "six sigma", "sap", "scrum", "project management",
    "hr", "recruitment", "talent acquisition",
    "autocad", "solidworks", "creo", "ansys",
    "supply chain", "logistics", "procurement",
}

# ============================================================================
# Consulting firms (JD explicitly flags entire-career-at-consulting as red flag)
# ============================================================================
CONSULTING_FIRMS = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "tech mahindra", "hcl", "hcl technologies", "mindtree",
    "mphasis", "l&t infotech", "ltimindtree", "persistent systems",
    "hexaware", "cyient", "zensar", "niit technologies",
    "virtusa", "larsen & toubro infotech",
}

# Product companies get a bonus
PRODUCT_COMPANIES = {
    "google", "microsoft", "amazon", "meta", "facebook", "apple",
    "netflix", "uber", "airbnb", "twitter", "x",
    "flipkart", "swiggy", "zomato", "ola", "razorpay",
    "phonepe", "paytm", "cred", "zerodha", "groww",
    "freshworks", "zoho", "postman", "browserstack",
    "atlassian", "adobe", "salesforce", "stripe", "square",
    "databricks", "snowflake", "datadog", "elastic",
    "huggingface", "hugging face", "openai", "anthropic", "cohere",
    "meesho", "dream11", "upstox", "unacademy",
    "sharechat", "dailyhunt", "myntra", "nykaa",
    "redrob",
    # Also small product startups (matched by company_size)
    "pied piper",  # Fictional but in dataset as startup
}

# ============================================================================
# Location scoring
# ============================================================================
LOCATION_TIER_SCORES = {
    # Tier 1: Preferred (JD says Pune/Noida)
    "pune": 1.0,
    "noida": 1.0,
    # Tier 2: Delhi NCR (JD says "Delhi NCR welcome")
    "delhi": 0.95,
    "new delhi": 0.95,
    "gurgaon": 0.95,
    "gurugram": 0.95,
    "greater noida": 0.95,
    "faridabad": 0.92,
    "ghaziabad": 0.92,
    # Tier 3: Other Tier-1 Indian cities (JD says "Hyderabad, Mumbai welcome")
    "bangalore": 0.85,
    "bengaluru": 0.85,
    "hyderabad": 0.85,
    "mumbai": 0.85,
    # Tier 4: Other major Indian cities
    "chennai": 0.78,
    "kolkata": 0.75,
    "ahmedabad": 0.72,
    "jaipur": 0.70,
    "lucknow": 0.70,
    "chandigarh": 0.72,
    "indore": 0.68,
    "kochi": 0.68,
    "coimbatore": 0.65,
    "thiruvananthapuram": 0.65,
    "bhopal": 0.65,
    "nagpur": 0.65,
    "visakhapatnam": 0.65,
}

INDIA_OTHER_RELOCATE = 0.65
INDIA_OTHER_NO_RELOCATE = 0.35
OUTSIDE_INDIA_RELOCATE = 0.25
OUTSIDE_INDIA_NO_RELOCATE = 0.08

INDIA_COUNTRY = "india"

# ============================================================================
# Experience scoring
# ============================================================================
# JD says 5-9 years, but flexible. Disqualifiers at extremes.
EXPERIENCE_IDEAL_MIN = 5.0
EXPERIENCE_IDEAL_MAX = 9.0
EXPERIENCE_ACCEPTABLE_MIN = 3.0
EXPERIENCE_ACCEPTABLE_MAX = 14.0
EXPERIENCE_HARD_MIN = 1.5
EXPERIENCE_HARD_MAX = 20.0

# ============================================================================
# Career description keyword analysis
# ============================================================================
STRONG_POSITIVE_KEYWORDS = [
    "ranking system", "retrieval system", "recommendation system",
    "search system", "matching system", "candidate matching",
    "embeddings", "vector search", "semantic search",
    "hybrid search", "dense retrieval", "re-ranking",
    "deployed", "production", "shipped", "launched",
    "end-to-end", "real-time", "real time",
    "inference", "model serving", "latency",
    "a/b test", "a/b testing", "ndcg", "evaluation framework",
    "recruiter", "talent", "hiring",
    "information retrieval",
]

MODERATE_POSITIVE_KEYWORDS = [
    "machine learning", "deep learning", "neural network",
    "nlp", "natural language", "text classification",
    "transformer", "fine-tun", "training pipeline",
    "feature engineering", "model training",
    "data pipeline", "ml pipeline", "ml model",
    "classification", "clustering", "regression",
    "prediction", "recommendation",
    "api", "microservice", "backend system",
    "python", "pytorch", "tensorflow",
    "distributed", "scalab", "high-throughput",
    "benchmark", "metric", "evaluation",
]

NEGATIVE_CAREER_KEYWORDS = [
    "marketing campaign", "brand identity", "seo strategy",
    "content writing", "content marketing", "editorial",
    "accounting", "financial reporting", "tax filing",
    "general ledger", "audit", "gaap", "ind-as",
    "sales cycle", "quota", "revenue target", "arr",
    "customer support", "ticket", "escalation process",
    "hr", "recruitment process", "talent acquisition team",
    "mechanical engineering", "cad", "solidworks", "ansys",
    "civil engineering", "construction",
    "packaging design", "brand design", "creative direction",
    "warehouses", "fulfillment", "logistics",
    "slide-craft", "excel modeling",
]

# ============================================================================
# Behavioral signal thresholds
# ============================================================================
REFERENCE_DATE = date(2026, 6, 17)  # "Current" date for recency calculations

# Last active date thresholds (days ago)
ACTIVE_VERY_RECENT_DAYS = 30    # Active within 30 days
ACTIVE_RECENT_DAYS = 90         # Active within 90 days
ACTIVE_STALE_DAYS = 180         # Inactive for 6+ months

# Response rate thresholds
RESPONSE_RATE_EXCELLENT = 0.7
RESPONSE_RATE_GOOD = 0.5
RESPONSE_RATE_POOR = 0.2

# Response time thresholds (hours)
RESPONSE_TIME_FAST = 24
RESPONSE_TIME_OK = 72
RESPONSE_TIME_SLOW = 120

# Notice period thresholds (days)
NOTICE_IDEAL = 30
NOTICE_ACCEPTABLE = 60
NOTICE_LONG = 90
NOTICE_VERY_LONG = 120

# ============================================================================
# Honeypot detection thresholds
# ============================================================================
HONEYPOT_EXPERT_SKILL_COUNT = 8       # Suspicious if 8+ expert skills
HONEYPOT_MIN_DURATION_FOR_EXPERT = 6  # Expert with <6 months = suspicious
HONEYPOT_ZERO_DURATION_EXPERT = 3     # 3+ expert skills with 0 duration = honeypot
HONEYPOT_ASSESSMENT_FAIL_THRESHOLD = 40  # Expert claiming but scores < 40

# ============================================================================
# Pre-filter thresholds
# ============================================================================
PREFILTER_MIN_EXPERIENCE = 1.0
PREFILTER_MAX_EXPERIENCE = 25.0
