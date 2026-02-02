import asyncio
from typing import List
from backend.services.bi_encoder import create_embedding
from backend.services.cross_encoder import rerank_documents, find_similarities
from backend.services.llm import ask_llm
from backend.core.database import ai_responses as ai_response_col
from backend.core.database import document_chunks as doc_chunk_col

#  Memory Retrieval
async def fetch_memory_context(query: str, query_vector: List[float], company_id: int) -> List[str]:
    pipeline = [
        {"$vectorSearch": {
            "index": "ai_responses_vector_index",
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": 50, "limit": 20,
            "filter": {"company_id": company_id}
        }},
        {"$project": {"_id": 0, "canonical_prompt": 1, "response": 1, "status": 1}}
    ]
    results = await ai_response_col.aggregate(pipeline).to_list(20)
    if not results: return []

    memory_map = {m["canonical_prompt"]: m for m in results}
    hits = find_similarities(query, list(memory_map.keys()), top_n=2)
    
    sections = []
    for hit in hits:
        m = memory_map.get(hit)
        label = {
            "canonical": "Verified Good Answer",
            "quarantine": "AVOID THIS - INCORRECT PREVIOUS ANSWER"
        }.get(m["status"], "Previous Draft Answer")
        
        sections.append(f"[{label}]: {m['response']}")
    return sections

# Document Retrieval
async def fetch_document_context(query: str, query_vector: List[float], company_id: int) -> List[str]:
    pipeline = [
        {"$vectorSearch": {
            "index": "docs_vector_index",
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": 200, "limit": 50,
            "filter": {"company_id": company_id}
        }},
        {"$project": {"_id": 0, "content": 1}}
    ]
    results = await doc_chunk_col.aggregate(pipeline).to_list(50)
    if not results: return []

    raw_chunks = [d["content"] for d in results]
    top_chunks = rerank_documents(query, raw_chunks, top_n=5)
    return [f"[Document Knowledge]: {chunk}" for chunk in top_chunks]

# Main Pipeline
async def run_rag_pipeline(query: str, company_id: int) -> str:
    query_vector = create_embedding(f"query: {query}")

    memory_task = fetch_memory_context(query, query_vector, company_id)
    docs_task = fetch_document_context(query, query_vector, company_id)
    
    memory_sections, doc_sections = await asyncio.gather(memory_task, docs_task)
    
    all_context = memory_sections + doc_sections

    final_prompt = f"Context:\n{'\n\n'.join(all_context)}\n\nQuestion: {query}\nAnswer:"
    return ask_llm(final_prompt)