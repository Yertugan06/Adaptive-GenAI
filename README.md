

# Adaptive GenAI Platform

**Version:** 0.1.0
**Author:** Yertugan Tb (Backend), Murat (Frontend)
**License:** MIT

A **hybrid Retrieval-Augmented Generation (RAG) system** for enterprise-grade question answering. Combines Google Gemini API, vector search, and feedback-based adaptive AI responses for multi-tenant environments.

---

## 🚀 Project Overview

Adaptive GenAI is designed to provide **accurate, reusable AI responses** using a combination of:

* **Vector retrieval:** Semantic search of AI responses and document chunks
* **Re-ranking:** Cross-encoder scoring for precision
* **Bayesian feedback:** Prioritizing helpful answers while avoiding bias from one-off high ratings
* **Multi-database design:** PostgreSQL for structured audits & MongoDB for vectorized knowledge storage
* **Local ML hosting:** Avoids third-party API costs while retaining full control

This project is suitable for **B2B or B2G AI support systems** where privacy, accuracy, and auditability are critical.

---

## 📦 Architecture

### 1. Polyglot Persistence

| Layer          | Database   | Purpose                                                     |
| -------------- | ---------- | ----------------------------------------------------------- |
| Relational     | PostgreSQL | Users, Companies, Generation Events, Audits                 |
| NoSQL / Vector | MongoDB    | AI Responses, Document Chunks, Prompt Events, Company Stats |

---

### 2. Hybrid-RAG Pipeline

1. **Prompt Processing**

   * Summarize query if token length > 500
   * Convert query into vector embedding (`bi-encoder`)

2. **Memory Retrieval**

   * Fetch previous AI responses for the company
   * Use semantic similarity + Bayesian score ranking

3. **Document Retrieval**

   * Vector search on document chunks
   * Cross-encoder re-ranking to select top relevant content

4. **LLM Generation**

   * Provide the context + prompt to a Google Gemini API
   * Store AI response in MongoDB for reuse

5. **Feedback Loop**

   * Users rate responses (1–5)
   * Update **Bayesian score**, `reuse_count`, and `status`
   * Promote responses to **canonical**, **quarantine**, or leave as **candidate**

---

### 3. Indexing & Optimization

* **Vector Search Index:** ANN (HNSW) on `embedding` fields for AI responses and document chunks
* **Compound Metadata Indexes:** `{ company_id: 1, created_at: -1 }` & `{ status: 1, bayesian_score: -1 }`
* **Smart Cache:** Cached canonical AI responses minimize unnecessary LLM calls
* **PostgreSQL Optimizations:** FK indexing, partial indexes for `rating IS NOT NULL`, lean storage of Mongo event IDs

---

## 🛠️ Features

* Multi-tenant support with per-company AI response isolation
* Adaptive AI response ranking based on Bayesian rating
* Full audit logging of prompt events and AI responses
* Multi-stage retrieval: memory + document context + LLM
* REST API with endpoints for prompts, responses, feedback, analytics
* Local ML hosting for embeddings and reranking

---

## 🗂️ Folder Structure

```
📦backend
 ┣ 📂api/v1          # FastAPI endpoints (auth, prompts, responses, feedback, analytics)
 ┣ 📂core            # DB connections, configuration
 ┣ 📂crud            # MongoDB + PostgreSQL CRUD operations
 ┣ 📂ml_models       # bi-encoder, reranker
 ┣ 📂schemas         # Pydantic models for NoSQL and SQL
 ┣ 📂services        # ML pipelines, RAG, embedding, LLM calls, feedback
 ┣ 📂storage         # Raw PDFs and document chunks
 ┣ 📜main.py         # FastAPI app entry
 ┣ 📜requirements.txt
```

---

## ⚡ Tech Stack

* **Python 3.12**, **FastAPI**
* **MongoDB** for vector and semi-structured storage
* **PostgreSQL** for relational audits
* **PyTorch / Transformers** for local bi-encoder & cross-encoder
* **Local LLM** (configurable in `/ml_models`) for answer generation
* **AsyncIO** for concurrent retrieval and LLM calls
* **Pydantic** for validation and serialization

---

## 🔑 API Overview

| Endpoint                                 | Method | Description                    |
| ---------------------------------------- | ------ | ------------------------------ |
| `/api/v1/auth/login`                     | POST   | Login user, get JWT            |
| `/api/v1/auth/register`                  | POST   | Register new user              |
| `/api/v1/prompts/submit`                 | POST   | Submit a query                 |
| `/api/v1/feedback/submit`                | POST   | Submit user feedback           |
| `/api/v1/feedback/history`               | GET    | Retrieve user feedback history |
| `/api/v1/responses/{res_id}`   | GET    | Get AI response                |
| `/api/v1/responses/search`     | GET    | Search AI responses            |
| `/api/v1/analytics/company/{company_id}` | GET    | Company dashboard analytics    |

---

## 🧑‍💻 Contributors

* **Yertugan Tb:** Backend, ML pipeline, RAG orchestration, AI response management
* **Murat:** Frontend, API integration, UI & UX

---

## ⚙️ Installation

```bash
# Clone the repo
git clone <repo-url>
cd backend

# Create venv and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run FastAPI server
uvicorn main:app --reload
```

---

## 📝 Notes

* Ensure MongoDB and PostgreSQL are running locally or via Docker
* Place ML models in `/ml_models` as per README instructions for embeddings and reranking
* Tokenization and embedding may require GPU for speed
* Company stats and caching improve performance over time

