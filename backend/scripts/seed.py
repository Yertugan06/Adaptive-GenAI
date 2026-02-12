import asyncio
import hashlib
import logging
from datetime import datetime
from bson import ObjectId
from sqlalchemy import text
from dateutil import parser

# Import your existing services
from backend.services.bi_encoder import create_embedding, count_tokens
from backend.services.llm import summarize, TOKENIZER
from backend.core.database import get_sql_db, mongo_db, engine
from backend.schemas.sql import Base


ai_responses_col = mongo_db.ai_responses
prompt_events_col = mongo_db.prompt_events
company_stats_col = mongo_db.company_stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- HELPER FUNCTIONS ---
def get_oid(short_id: str) -> ObjectId:
    """Converts short string to a deterministic 24-char ObjectId"""
    hex_str = hashlib.md5(short_id.encode()).hexdigest()[:24]
    return ObjectId(hex_str)

def get_date(date_str: str) -> datetime:
    """Parses ISO strings with timezone support"""
    return parser.isoparse(date_str)

def truncate_for_embedding(text: str, max_tokens: int = 500) -> str:
    """Truncate text to fit within embedding model's token limit"""
    tokens = TOKENIZER.encode(text)
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        return TOKENIZER.decode(truncated_tokens)
    return text

def generate_real_embedding(text: str) -> list[float]:
    """Generate real embedding for text, truncating if necessary"""
    # Truncate text to avoid token limit issues
    truncated_text = truncate_for_embedding(text)
    
    # For E5 model, we should prefix with appropriate instruction
    # According to E5 documentation, for retrieval we should use "passage: " prefix
    embedding_text = f"passage: {truncated_text}"
    
    try:
        embedding = create_embedding(embedding_text)
        logger.debug(f"Generated embedding of length {len(embedding)}")
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        # Fallback to dummy embedding
        return [0.1] * 768

async def generate_summary_for_response(response_text: str) -> str:
    """Generate a summary for long response text if needed"""
    # Count tokens in response
    token_count = count_tokens(response_text)
    
    # If response is very long, generate a summary
    if token_count > 300:
        try:
            summary = await summarize(response_text)
            logger.debug(f"Generated summary for long response (original: {token_count} tokens)")
            return summary
        except Exception as e:
            logger.warning(f"Failed to generate summary: {e}")
    
    return response_text

# --- COMPLETE DATA ---
COMPANIES = [
    {"id": 1, "name": "TechFlow Analytics", "industry": "AI/ML Consulting", "plan_tier": "enterprise", "created_at": "2024-06-01T09:00:00Z"},
    {"id": 2, "name": "DataSphere Solutions", "industry": "Data Engineering", "plan_tier": "standard", "created_at": "2024-07-15T10:30:00Z"}
]

USERS = [
    {"id": 1, "company_id": 1, "name": "Alex Chen", "email": "alex.chen@techflow.com", "role": "ML Engineer","hashed_password" : "$2b$12$YIFPhp7mZz.VSoXrAbFFPOpF/ATCjljL3upkGKF.z63zofyz28FzS","created_at": "2024-06-02T08:00:00Z"},
    {"id": 2, "company_id": 1, "name": "Sarah Johnson", "email": "sarah.johnson@techflow.com", "role": "Data Scientist","hashed_password" : "$2b$12$YIFPhp7mZz.VSoXrAbFFPOpF/ATCjljL3upkGKF.z63zofyz28FzS", "created_at": "2024-06-03T09:15:00Z"},
    {"id": 3, "company_id": 1, "name": "Marcus Rodriguez", "email": "marcus.rodriguez@techflow.com", "role": "Engineering Manager","hashed_password" : "$2b$12$YIFPhp7mZz.VSoXrAbFFPOpF/ATCjljL3upkGKF.z63zofyz28FzS", "created_at": "2024-06-05T11:00:00Z"},
    {"id": 4, "company_id": 1, "name": "Jamie Wilson", "email": "jamie.wilson@techflow.com", "role": "AI Research Intern","hashed_password" : "$2b$12$YIFPhp7mZz.VSoXrAbFFPOpF/ATCjljL3upkGKF.z63zofyz28FzS", "created_at": "2024-08-01T13:00:00Z"},
    {"id": 5, "company_id": 2, "name": "Priya Sharma", "email": "priya.sharma@datasphere.com", "role": "Senior Data Engineer","hashed_password" : "$2b$12$YIFPhp7mZz.VSoXrAbFFPOpF/ATCjljL3upkGKF.z63zofyz28FzS", "created_at": "2024-07-20T14:00:00Z"}
]

# AI Responses with full content and all fields
AI_RESPONSES = [
    # Company 1 Responses
    {
        "_id": "A001",
        "canonical_prompt": "Explain gradient descent simply",
        "response": "Gradient descent is an optimization algorithm used to minimize a function by iteratively moving in the direction of steepest descent as defined by the negative of the gradient. Think of it like hiking down a mountain: at each step, you look for the steepest downhill direction and take a small step that way. In machine learning, we use it to find the parameters that minimize our loss function. The learning rate controls how big each step is - too small and you'll take forever, too big and you might overshoot the minimum.",
        "aliases": [
            "What is gradient descent?",
            "Explain gradient descent intuitively",
            "How does gradient descent work?",
            "Simple explanation of gradient descent"
        ],
        "topics": ["machine-learning", "optimization", "neural-networks"],
        "source_doc_ids": [],
        "company_id": 1,
        "model": "gemini-1.5-pro",
        "status": "canonical",
        "reuse_count": 8,
        "rating_sum": 38,
        "bayesian_score": 4.42,
        "created_at": "2024-06-10T10:00:00Z",
        "updated_at": "2025-01-15T14:30:00Z"
    },
    {
        "_id": "A002",
        "canonical_prompt": "Difference between lists and tuples in Python",
        "response": "Lists are mutable (can be modified after creation) while tuples are immutable (cannot be modified). Lists use square brackets [], tuples use parentheses (). Because tuples are immutable, they can be used as dictionary keys, while lists cannot. Tuples are generally faster for iteration. Use lists when you need a collection that changes, tuples when you need a fixed collection of items.",
        "aliases": [
            "Python list vs tuple",
            "When to use list or tuple?",
            "Mutable vs immutable collections",
            "Compare list and tuple in Python"
        ],
        "topics": ["python", "programming", "data-structures"],
        "source_doc_ids": [],
        "company_id": 1,
        "model": "gemini-1.5-flash",
        "status": "canonical",
        "reuse_count": 15,
        "rating_sum": 68,
        "bayesian_score": 4.35,
        "created_at": "2024-06-12T11:30:00Z",
        "updated_at": "2025-01-18T16:45:00Z"
    },
    {
        "_id": "A003",
        "canonical_prompt": "How to visualize correlation in pandas",
        "response": "You can visualize correlations in pandas using: 1) `df.corr()` to compute the correlation matrix, then visualize with seaborn's heatmap: `sns.heatmap(df.corr(), annot=True)`. 2) Scatter matrix: `pd.plotting.scatter_matrix(df)`. 3) Pairplot for pairwise relationships: `sns.pairplot(df)`. 4) Individual scatter plots with regression lines using `sns.regplot()`. Heatmaps are best for seeing all correlations at once, while scatter plots show the actual data distribution.",
        "aliases": [
            "Correlation visualization pandas",
            "Plot correlation matrix Python",
            "Best way to show correlations",
            "Heatmap for correlation in dataframe"
        ],
        "topics": ["data-visualization", "pandas", "data-science"],
        "source_doc_ids": [],
        "company_id": 1,
        "model": "gemini-1.5-pro",
        "status": "canonical",
        "reuse_count": 12,
        "rating_sum": 55,
        "bayesian_score": 4.38,
        "created_at": "2024-06-15T14:20:00Z",
        "updated_at": "2025-01-20T10:15:00Z"
    },
    {
        "_id": "A004",
        "canonical_prompt": "Docker vs Kubernetes comparison",
        "response": "Docker is a containerization platform that packages applications and dependencies into containers. Kubernetes is a container orchestration system that manages multiple containers across multiple hosts. Docker is like shipping containers for software, while Kubernetes is like the port management system that handles loading, routing, and scaling of those containers. Use Docker to create and run containers locally. Use Kubernetes when you need to manage many containers in production with features like auto-scaling, load balancing, and self-healing.",
        "aliases": [
            "Difference between Docker and Kubernetes",
            "When to use Docker vs Kubernetes?",
            "Containerization vs orchestration",
            "Compare container technologies"
        ],
        "topics": ["devops", "cloud", "containers", "deployment"],
        "source_doc_ids": [],
        "company_id": 1,
        "model": "gemini-1.5-pro",
        "status": "canonical",
        "reuse_count": 7,
        "rating_sum": 32,
        "bayesian_score": 4.25,
        "created_at": "2024-06-18T16:45:00Z",
        "updated_at": "2025-01-22T11:30:00Z"
    },
    {
        "_id": "A005",
        "canonical_prompt": "How to optimize slow SQL queries",
        "response": "To optimize slow SQL queries: 1) Add indexes on frequently filtered columns. 2) Avoid SELECT * - specify only needed columns. 3) Use EXPLAIN to analyze query plans. 4) Avoid N+1 queries with JOINs. 5) Use WHERE instead of HAVING for filtering. 6) Limit results with pagination. 7) Avoid functions on indexed columns in WHERE clauses. 8) Normalize/denormalize appropriately. 9) Use query caching. 10) Consider partitioning large tables.",
        "aliases": [
            "SQL query optimization tips",
            "Make SQL queries faster",
            "Database performance tuning",
            "Indexing strategies for SQL"
        ],
        "topics": ["sql", "databases", "performance", "data-engineering"],
        "source_doc_ids": [],
        "company_id": 1,
        "model": "gemini-1.5-flash",
        "status": "canonical",
        "reuse_count": 9,
        "rating_sum": 42,
        "bayesian_score": 4.33,
        "created_at": "2024-06-20T13:15:00Z",
        "updated_at": "2025-01-25T09:45:00Z"
    },
    {
        "_id": "A006",
        "canonical_prompt": "Mitigate bias in machine learning models",
        "response": "To mitigate bias in ML models: 1) Audit training data for representation gaps. 2) Use fairness metrics during evaluation. 3) Apply techniques like reweighting, adversarial debiasing, or preprocessing. 4) Include diverse stakeholders in development. 5) Implement continuous monitoring in production. 6) Use interpretability tools to understand model decisions. 7) Consider differential privacy for sensitive data. Bias mitigation is an ongoing process, not a one-time fix.",
        "aliases": [
            "Reduce bias in AI models",
            "AI fairness techniques",
            "Ethical machine learning practices",
            "Address dataset bias"
        ],
        "topics": ["ai-ethics", "machine-learning", "fairness", "responsible-ai"],
        "source_doc_ids": [],
        "company_id": 1,
        "model": "gemini-1.5-pro",
        "status": "canonical",
        "reuse_count": 5,
        "rating_sum": 23,
        "bayesian_score": 4.15,
        "created_at": "2024-06-22T15:30:00Z",
        "updated_at": "2025-01-28T14:20:00Z"
    },
    {
        "_id": "A007",
        "canonical_prompt": "Basic MLOps pipeline setup",
        "response": "A basic MLOps pipeline includes: 1) Version control for code and data. 2) Automated testing for models. 3) CI/CD for model deployment. 4) Model registry for tracking versions. 5) Monitoring for model drift and performance. 6) Feature stores for consistent features. Start with Git + GitHub Actions for CI/CD, MLflow for experiment tracking, Docker for containerization, and a cloud service like AWS SageMaker or Azure ML for orchestration. Keep it simple initially and expand as needed.",
        "aliases": [
            "How to set up MLOps?",
            "Machine learning deployment pipeline",
            "MLOps best practices",
            "Model deployment workflow"
        ],
        "topics": ["mlops", "model-deployment", "devops", "machine-learning"],
        "source_doc_ids": [],
        "company_id": 1,
        "model": "gemini-1.5-pro",
        "status": "canonical",
        "reuse_count": 6,
        "rating_sum": 28,
        "bayesian_score": 4.20,
        "created_at": "2024-06-25T10:45:00Z",
        "updated_at": "2025-01-30T16:10:00Z"
    },
    {
        "_id": "A008",
        "canonical_prompt": "Calculate ROI for AI projects",
        "response": "ROI for AI projects = (Benefits - Costs) / Costs. Benefits include: increased revenue, cost savings, productivity gains, improved customer satisfaction. Costs include: data acquisition, talent, infrastructure, maintenance. Track both tangible metrics (revenue increase, cost reduction) and intangible benefits (decision speed, error reduction). Use a phased approach with pilot projects to demonstrate value before scaling. Typical AI project ROI ranges from 200-500% over 2-3 years.",
        "aliases": [
            "AI project business value",
            "Measuring AI success metrics",
            "Business case for AI implementation",
            "Cost-benefit analysis AI"
        ],
        "topics": ["business-strategy", "roi", "project-management", "ai"],
        "source_doc_ids": [],
        "company_id": 1,
        "model": "gemini-1.5-pro",
        "status": "canonical",
        "reuse_count": 4,
        "rating_sum": 19,
        "bayesian_score": 4.10,
        "created_at": "2024-06-28T14:00:00Z",
        "updated_at": "2025-02-01T13:45:00Z"
    },
    # Company 2 Responses
    {
        "_id": "B001",
        "canonical_prompt": "ETL pipeline best practices",
        "response": "ETL best practices: 1) Design for idempotency - reruns should produce same results. 2) Implement comprehensive logging and monitoring. 3) Handle failures gracefully with retry logic. 4) Use incremental loads where possible. 5) Validate data quality at each stage. 6) Separate transformation logic from extraction/loading. 7) Use version control for pipeline code. 8) Implement data lineage tracking. 9) Test with sample data before full runs. 10) Document data transformations thoroughly.",
        "aliases": [
            "How to build robust ETL?",
            "Data pipeline design patterns",
            "ETL pipeline architecture",
            "Data integration best practices"
        ],
        "topics": ["data-engineering", "etl", "pipelines", "data-warehousing"],
        "source_doc_ids": [],
        "company_id": 2,
        "model": "gemini-1.5-pro",
        "status": "canonical",
        "reuse_count": 11,
        "rating_sum": 52,
        "bayesian_score": 4.40,
        "created_at": "2024-07-25T09:30:00Z",
        "updated_at": "2025-01-15T11:20:00Z"
    },
    {
        "_id": "B002",
        "canonical_prompt": "Apache Spark optimization techniques",
        "response": "Spark optimization: 1) Use appropriate partitioning to avoid skew. 2) Cache frequently used DataFrames. 3) Use broadcast joins for small tables. 4) Select proper serialization (Kryo). 5) Tune memory settings (executor memory, driver memory). 6) Use DataFrame API over RDD for Catalyst optimization. 7) Implement checkpointing for long lineages. 8) Use adaptive query execution (AQE) in Spark 3.0+. 9) Minimize shuffles. 10) Use efficient data formats (Parquet/ORC). Monitor with Spark UI to identify bottlenecks.",
        "aliases": [
            "Make Spark jobs faster",
            "Spark performance tuning",
            "Big data processing optimization",
            "Distributed computing best practices"
        ],
        "topics": ["spark", "big-data", "performance", "data-engineering"],
        "source_doc_ids": [],
        "company_id": 2,
        "model": "gemini-1.5-pro",
        "status": "canonical",
        "reuse_count": 9,
        "rating_sum": 43,
        "bayesian_score": 4.32,
        "created_at": "2024-07-28T14:45:00Z",
        "updated_at": "2025-01-18T15:30:00Z"
    },
    {
        "_id": "B003",
        "canonical_prompt": "Data warehouse vs data lake",
        "response": "Data warehouses store structured, processed data in schemas optimized for analytics (OLAP). Data lakes store raw data in any format (structured, semi-structured, unstructured). Warehouses are for business intelligence, lakes for big data processing and machine learning. Modern approach: data lakehouse - combines both capabilities. Choose warehouse for governed analytics, lake for exploratory analysis and ML, lakehouse for both needs.",
        "aliases": [
            "Difference between data lake and warehouse",
            "When to use data lake vs warehouse?",
            "Data storage architecture comparison",
            "Modern data platform design"
        ],
        "topics": ["data-architecture", "data-warehousing", "data-lake", "storage"],
        "source_doc_ids": [],
        "company_id": 2,
        "model": "gemini-1.5-flash",
        "status": "canonical",
        "reuse_count": 8,
        "rating_sum": 37,
        "bayesian_score": 4.28,
        "created_at": "2024-08-01T11:20:00Z",
        "updated_at": "2025-01-22T10:15:00Z"
    },
    # Candidate/Quarantine Responses
    {
        "_id": "C001",
        "canonical_prompt": "Implement real-time data streaming",
        "response": "For real-time streaming: use Apache Kafka for message queuing, Spark Streaming or Flink for processing, and a sink like Elasticsearch or a database for storage. Design for exactly-once processing semantics where possible. Consider latency vs throughput tradeoffs. Monitor consumer lag and processing rates. Implement backpressure handling for bursty data.",
        "aliases": [
            "Real-time data processing setup",
            "Streaming architecture patterns",
            "How to process live data?"
        ],
        "topics": ["streaming", "real-time", "data-engineering", "kafka"],
        "source_doc_ids": [],
        "company_id": 1,
        "model": "gemini-1.5-pro",
        "status": "candidate",
        "reuse_count": 3,
        "rating_sum": 12,
        "bayesian_score": 3.85,
        "created_at": "2025-01-05T14:30:00Z",
        "updated_at": "2025-01-25T16:20:00Z"
    },
    {
        "_id": "C002",
        "canonical_prompt": "Python memory management tips",
        "response": "To manage Python memory: use generators for large datasets, delete unused objects with del, use __slots__ to reduce instance memory, avoid circular references, use efficient data structures (arrays vs lists), profile with memory_profiler, consider PyPy for memory efficiency, use weak references for caches.",
        "aliases": [
            "Reduce Python memory usage",
            "Memory optimization in Python",
            "Python garbage collection tips"
        ],
        "topics": ["python", "performance", "memory", "optimization"],
        "source_doc_ids": [],
        "company_id": 1,
        "model": "gemini-1.5-flash",
        "status": "quarantine",
        "reuse_count": 2,
        "rating_sum": 6,
        "bayesian_score": 2.90,
        "created_at": "2024-12-15T10:15:00Z",
        "updated_at": "2025-01-10T11:45:00Z",
        "quarantine_reason": "Low average rating from users"
    }
]

# Complete Prompt Events (25 documents)
PROMPT_EVENTS = [
    # Company 1 Events
    {"_id": "P101", "prompt_text": "What is gradient descent?", "ai_response_ids": ["A001"], "user_id": 1, "company_id": 1, "rating": 5, "used_cached_answer": True, "created_at": "2025-01-12T10:30:00Z"},
    {"_id": "P102", "prompt_text": "Explain gradient descent intuitively", "ai_response_ids": ["A001"], "user_id": 4, "company_id": 1, "rating": 4, "used_cached_answer": True, "created_at": "2025-01-12T14:15:00Z"},
    {"_id": "P103", "prompt_text": "Python list vs tuple", "ai_response_ids": ["A002"], "user_id": 4, "company_id": 1, "rating": 5, "used_cached_answer": True, "created_at": "2025-01-13T09:45:00Z"},
    {"_id": "P104", "prompt_text": "When should I use a tuple instead of a list?", "ai_response_ids": ["A002"], "user_id": 2, "company_id": 1, "rating": 4, "used_cached_answer": True, "created_at": "2025-01-13T11:20:00Z"},
    {"_id": "P105", "prompt_text": "How to show correlations in my dataframe?", "ai_response_ids": ["A003"], "user_id": 2, "company_id": 1, "rating": 5, "used_cached_answer": True, "created_at": "2025-01-14T15:30:00Z"},
    {"_id": "P106", "prompt_text": "What's the difference between Docker and Kubernetes?", "ai_response_ids": ["A004"], "user_id": 3, "company_id": 1, "rating": 4, "used_cached_answer": True, "created_at": "2025-01-15T10:00:00Z"},
    {"_id": "P107", "prompt_text": "My SQL query is slow, how to optimize?", "ai_response_ids": ["A005"], "user_id": 1, "company_id": 1, "rating": 5, "used_cached_answer": True, "created_at": "2025-01-16T13:45:00Z"},
    {"_id": "P108", "prompt_text": "How to reduce bias in our ML models?", "ai_response_ids": ["A006"], "user_id": 3, "company_id": 1, "rating": 4, "used_cached_answer": True, "created_at": "2025-01-17T16:20:00Z"},
    {"_id": "P109", "prompt_text": "Setup for MLOps pipeline", "ai_response_ids": ["A007"], "user_id": 1, "company_id": 1, "rating": 5, "used_cached_answer": True, "created_at": "2025-01-18T09:15:00Z"},
    {"_id": "P110", "prompt_text": "Calculate AI project ROI", "ai_response_ids": ["A008"], "user_id": 3, "company_id": 1, "rating": 4, "used_cached_answer": True, "created_at": "2025-01-19T14:30:00Z"},
    {"_id": "P111", "prompt_text": "Explain overfitting in simple terms", "ai_response_ids": ["NEW001"], "user_id": 4, "company_id": 1, "rating": 5, "used_cached_answer": False, "created_at": "2025-01-20T11:45:00Z"},
    {"_id": "P112", "prompt_text": "Best practices for code documentation", "ai_response_ids": ["NEW002"], "user_id": 1, "company_id": 1, "rating": 4, "used_cached_answer": False, "created_at": "2025-01-21T15:10:00Z"},
    {"_id": "P113", "prompt_text": "How does a transformer model work?", "ai_response_ids": ["NEW003"], "user_id": 2, "company_id": 1, "rating": 5, "used_cached_answer": False, "created_at": "2025-01-22T10:25:00Z"},
    {"_id": "P114", "prompt_text": "Heatmap for correlation in pandas", "ai_response_ids": ["A003"], "user_id": 2, "company_id": 1, "rating": 4, "used_cached_answer": True, "created_at": "2025-01-23T13:40:00Z"},
    {"_id": "P115", "prompt_text": "Simple explanation of backpropagation", "ai_response_ids": ["NEW004"], "user_id": 4, "company_id": 1, "rating": 3, "used_cached_answer": False, "created_at": "2025-01-24T16:55:00Z"},
    # Company 2 Events
    {"_id": "P201", "prompt_text": "ETL pipeline design best practices", "ai_response_ids": ["B001"], "user_id": 5, "company_id": 2, "rating": 5, "used_cached_answer": True, "created_at": "2025-01-12T09:15:00Z"},
    {"_id": "P202", "prompt_text": "How to optimize Spark jobs?", "ai_response_ids": ["B002"], "user_id": 5, "company_id": 2, "rating": 4, "used_cached_answer": True, "created_at": "2025-01-13T14:30:00Z"},
    {"_id": "P203", "prompt_text": "Data lake vs data warehouse comparison", "ai_response_ids": ["B003"], "user_id": 5, "company_id": 2, "rating": 5, "used_cached_answer": True, "created_at": "2025-01-14T11:45:00Z"},
    {"_id": "P204", "prompt_text": "Real-time streaming implementation", "ai_response_ids": ["C001"], "user_id": 5, "company_id": 2, "rating": 4, "used_cached_answer": True, "created_at": "2025-01-15T16:20:00Z"},
    {"_id": "P205", "prompt_text": "Best data format for analytics", "ai_response_ids": ["NEW201"], "user_id": 5, "company_id": 2, "rating": 5, "used_cached_answer": False, "created_at": "2025-01-16T13:10:00Z"},
    {"_id": "P206", "prompt_text": "Data pipeline monitoring tools", "ai_response_ids": ["NEW202"], "user_id": 5, "company_id": 2, "rating": 4, "used_cached_answer": False, "created_at": "2025-01-17T10:35:00Z"},
    {"_id": "P207", "prompt_text": "How to build robust ETL?", "ai_response_ids": ["B001"], "user_id": 5, "company_id": 2, "rating": 5, "used_cached_answer": True, "created_at": "2025-01-18T15:50:00Z"},
    {"_id": "P208", "prompt_text": "Spark performance tuning guide", "ai_response_ids": ["B002"], "user_id": 5, "company_id": 2, "rating": 4, "used_cached_answer": True, "created_at": "2025-01-19T12:05:00Z"},
    {"_id": "P209", "prompt_text": "Modern data platform architecture", "ai_response_ids": ["B003"], "user_id": 5, "company_id": 2, "rating": 5, "used_cached_answer": True, "created_at": "2025-01-20T09:20:00Z"},
    {"_id": "P210", "prompt_text": "Data quality validation techniques", "ai_response_ids": ["NEW203"], "user_id": 5, "company_id": 2, "rating": 4, "used_cached_answer": False, "created_at": "2025-01-21T14:35:00Z"}
]

# SQL Generation Events (25 rows matching prompt events)
GEN_EVENTS_SQL = [
    (1, 'P101', 5, '2025-01-12 10:30:00'),
    (4, 'P102', 4, '2025-01-12 14:15:00'),
    (4, 'P103', 5, '2025-01-13 09:45:00'),
    (2, 'P104', 4, '2025-01-13 11:20:00'),
    (2, 'P105', 5, '2025-01-14 15:30:00'),
    (3, 'P106', 4, '2025-01-15 10:00:00'),
    (1, 'P107', 5, '2025-01-16 13:45:00'),
    (3, 'P108', 4, '2025-01-17 16:20:00'),
    (1, 'P109', 5, '2025-01-18 09:15:00'),
    (3, 'P110', 4, '2025-01-19 14:30:00'),
    (4, 'P111', 5, '2025-01-20 11:45:00'),
    (1, 'P112', 4, '2025-01-21 15:10:00'),
    (2, 'P113', 5, '2025-01-22 10:25:00'),
    (2, 'P114', 4, '2025-01-23 13:40:00'),
    (4, 'P115', 3, '2025-01-24 16:55:00'),
    (5, 'P201', 5, '2025-01-12 09:15:00'),
    (5, 'P202', 4, '2025-01-13 14:30:00'),
    (5, 'P203', 5, '2025-01-14 11:45:00'),
    (5, 'P204', 4, '2025-01-15 16:20:00'),
    (5, 'P205', 5, '2025-01-16 13:10:00'),
    (5, 'P206', 4, '2025-01-17 10:35:00'),
    (5, 'P207', 5, '2025-01-18 15:50:00'),
    (5, 'P208', 4, '2025-01-19 12:05:00'),
    (5, 'P209', 5, '2025-01-20 09:20:00'),
    (5, 'P210', 4, '2025-01-21 14:35:00')
]

# Company Stats
COMPANY_STATS = [
    {
        "company_id": 1,
        "total_rating_sum": 175.5,
        "total_review_count": 45,
        "company_avg_score": 3.90,
        "last_updated": "2025-01-25T10:00:00Z"
    },
    {
        "company_id": 2,
        "total_rating_sum": 89.0,
        "total_review_count": 23,
        "company_avg_score": 3.87,
        "last_updated": "2025-01-22T14:30:00Z"
    }
]

async def seed():
    """Main seeding function"""
    logger.info("🌱 Starting Database Seed...")
    
    # 1. SQL: Companies & Users
    # -----------------------------------------------
    Base.metadata.create_all(bind=engine)
    db_sql = next(get_sql_db())
    try:
        # Clear old data with proper order to respect foreign keys
        logger.info("Clearing old SQL data...")
        db_sql.execute(text("TRUNCATE TABLE generation_events RESTART IDENTITY CASCADE"))
        db_sql.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        db_sql.execute(text("TRUNCATE TABLE companies RESTART IDENTITY CASCADE"))
        
        # Reset sequences to start at 1 (will be updated after explicit inserts)
        db_sql.execute(text("ALTER SEQUENCE companies_id_seq RESTART WITH 1"))
        db_sql.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
        db_sql.execute(text("ALTER SEQUENCE generation_events_id_seq RESTART WITH 1"))
        
        # ---------- Insert companies ----------
        logger.info(f"Inserting {len(COMPANIES)} companies...")
        for c in COMPANIES:
            db_sql.execute(
                text("""
                    INSERT INTO companies (id, name, industry, plan_tier, created_at) 
                    VALUES (:id, :name, :industry, :plan_tier, :created_at)
                """),
                {
                    "id": c["id"],
                    "name": c["name"],
                    "industry": c["industry"],
                    "plan_tier": c["plan_tier"],
                    "created_at": get_date(c["created_at"])
                }
            )
        
        # ✅ Update companies sequence to the highest used id
        max_company_id = db_sql.execute(text("SELECT MAX(id) FROM companies")).scalar()
        db_sql.execute(
            text("SELECT setval('companies_id_seq', :max_id)"),
            {"max_id": max_company_id}
        )
        logger.info("✅ Companies sequence updated.")
        
        # ---------- Insert users ----------
        logger.info(f"Inserting {len(USERS)} users...")
        for u in USERS:
            db_sql.execute(
                text("""
                    INSERT INTO users (id, company_id, name, email, hashed_password, role, created_at) 
                    VALUES (:id, :company_id, :name, :email, :hashed_password, :role, :created_at)
                """),
                {
                    "id": u["id"],
                    "company_id": u["company_id"],
                    "name": u["name"],
                    "email": u["email"],
                    "hashed_password": u["hashed_password"],
                    "role": u["role"],
                    "created_at": get_date(u["created_at"])
                }
            )
        
        # ✅ Update users sequence to the highest used id
        max_user_id = db_sql.execute(text("SELECT MAX(id) FROM users")).scalar()
        db_sql.execute(
            text("SELECT setval('users_id_seq', :max_id)"),
            {"max_id": max_user_id}
        )
        logger.info("✅ Users sequence updated.")
        
        # ✅ Commit all SQL changes (data + sequence adjustments)
        db_sql.commit()
        logger.info("✅ SQL: Companies and users inserted successfully.")
        
    except Exception as e:
        db_sql.rollback()
        logger.error(f"❌ SQL Error: {e}")
        raise
    
    # 2. Mongo: AI Responses with REAL embeddings
    # -----------------------------------------------
    logger.info("Clearing AI responses collection...")
    await ai_responses_col.delete_many({})
    
    clean_responses = []
    logger.info(f"Processing {len(AI_RESPONSES)} AI responses with real embeddings...")
    
    for i, r in enumerate(AI_RESPONSES):
        logger.info(f"Generating embedding for response {r['_id']}...")
        
        # Generate real embedding from the response text
        embedding = generate_real_embedding(r["response"])
        
        # Generate a summary for the response if it's long
        summarized_response = generate_summary_for_response(r["response"])
        
        doc = {
            "_id": get_oid(r["_id"]),
            "canonical_prompt": r["canonical_prompt"],
            "response": summarized_response if summarized_response != r["response"] else r["response"],
            "embedding": embedding,
            "aliases": r.get("aliases", []),
            "topics": r.get("topics", []),
            "source_doc_ids": r.get("source_doc_ids", []),
            "company_id": r["company_id"],
            "model": r["model"],
            "status": r["status"],
            "reuse_count": r["reuse_count"],
            "rating_sum": r["rating_sum"],
            "bayesian_score": r["bayesian_score"],
            "created_at": get_date(r["created_at"]),
            "updated_at": get_date(r.get("updated_at", r["created_at"])),
            "schema_version": 1
        }
        
        # Add optional fields if they exist
        if "quarantine_reason" in r:
            doc["quarantine_reason"] = r["quarantine_reason"]
        
        clean_responses.append(doc)
        
        # Small delay to prevent overwhelming the embedding service
        if i % 3 == 0:
            await asyncio.sleep(0.05)
    
    if clean_responses:
        await ai_responses_col.insert_many(clean_responses)
        logger.info(f"✅ Mongo: Inserted {len(clean_responses)} AI responses with real embeddings.")
    
    # 3. Mongo: Prompt Events
    # -----------------------------------------------
    logger.info("Clearing prompt events collection...")
    await prompt_events_col.delete_many({})
    
    clean_prompts = []
    logger.info(f"Processing {len(PROMPT_EVENTS)} prompt events...")
    
    # Create a mapping of response short IDs to ObjectIds for linking
    response_id_map = {r["_id"]: get_oid(r["_id"]) for r in AI_RESPONSES}
    
    for p in PROMPT_EVENTS:
        # Convert response IDs, handling "NEW" responses by generating new ObjectIds
        response_ids = []
        for rid in p["ai_response_ids"]:
            if rid in response_id_map:
                response_ids.append(response_id_map[rid])
            else:
                # For "NEW" responses, generate a deterministic ObjectId
                response_ids.append(get_oid(rid))
        
        doc = {
            "_id": get_oid(p["_id"]),
            "prompt_text": p["prompt_text"],
            "ai_response_ids": response_ids,
            "user_id": p["user_id"],
            "company_id": p["company_id"],
            "rating": p["rating"],
            "used_cached_answer": p.get("used_cached_answer", True),
            "created_at": get_date(p["created_at"]),
            "schema_version": 1
        }
        clean_prompts.append(doc)
    
    if clean_prompts:
        await prompt_events_col.insert_many(clean_prompts)
        logger.info(f"✅ Mongo: Inserted {len(clean_prompts)} prompt events.")
    
    # 4. SQL: Generation Events (Audit Log)
    # -----------------------------------------------
    try:
        logger.info("Inserting generation events...")
        
        # Convert GEN_EVENTS_SQL to parameterized format
        for row in GEN_EVENTS_SQL:
            user_id, short_p_id, rating, date_str = row
            full_oid_str = str(get_oid(short_p_id))
            
            # Convert date string from "YYYY-MM-DD HH:MM:SS" to ISO format
            iso_date_str = date_str.replace(" ", "T") + "Z"
            
            db_sql.execute(
                text("""
                    INSERT INTO generation_events (user_id, mongo_event_id, rating, created_at) 
                    VALUES (:user_id, :mongo_event_id, :rating, :created_at)
                """),
                {
                    "user_id": user_id,
                    "mongo_event_id": full_oid_str,
                    "rating": rating,
                    "created_at": get_date(iso_date_str)
                }
            )
        
        db_sql.commit()
        logger.info(f"✅ SQL: Inserted {len(GEN_EVENTS_SQL)} generation audit logs.")
        
    except Exception as e:
        logger.error(f"❌ SQL Audit Log Error: {e}")
        db_sql.rollback()
        raise
    
    # 5. Mongo: Company Stats
    # -----------------------------------------------
    logger.info("Clearing company stats collection...")
    await company_stats_col.delete_many({})
    
    clean_stats = []
    for stat in COMPANY_STATS:
        doc = {
            "company_id": stat["company_id"],
            "total_rating_sum": stat["total_rating_sum"],
            "total_review_count": stat["total_review_count"],
            "company_avg_score": stat["company_avg_score"],
            "last_updated": get_date(stat["last_updated"])
        }
        clean_stats.append(doc)
    
    if clean_stats:
        await company_stats_col.insert_many(clean_stats)
        logger.info(f"✅ Mongo: Inserted {len(clean_stats)} company stats documents.")
    
    # 6. Verify embeddings
    # -----------------------------------------------
    logger.info("Verifying embeddings...")
    total_responses = await ai_responses_col.count_documents({})
    responses_with_embeddings = await ai_responses_col.count_documents({"embedding.0": {"$exists": True}})
    
    if total_responses == responses_with_embeddings:
        logger.info(f"✅ All {total_responses} responses have embeddings.")
        
        # Sample one embedding to verify dimensions
        sample_doc = await ai_responses_col.find_one({})
        if sample_doc and "embedding" in sample_doc:
            logger.info(f"✅ Sample embedding dimensions: {len(sample_doc['embedding'])}")
    else:
        logger.warning(f"⚠️ Only {responses_with_embeddings} out of {total_responses} responses have embeddings.")
    
    logger.info("🎉 Seed completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed())