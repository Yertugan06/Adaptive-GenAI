import asyncio
from typing import List, Tuple
from backend.services.bi_encoder import create_embedding
from backend.services.cross_encoder import rerank_documents, find_similarities
from backend.core.database import ai_responses as ai_response_col
from backend.core.database import document_chunks as doc_chunk_col
from backend.services.llm import DEFAULT_MODEL, summarize, ask_llm
from backend.services.bi_encoder import count_tokens
from backend.schemas.nosql.ai_response import AIResponse
from backend.schemas.nosql.prompt_event import PromptEvent
from backend.crud.ai_crud import create_ai_response, create_prompt_event, push_ai_response_to_event
from pydantic import BaseModel
import torch

class RAGResult(BaseModel):
    ai_response_id: str
    event_id: str
    response_text: str
    model: str
    feedback_required: bool = True

#  Memory Retrieval
async def fetch_memory_context(query: str, query_vector: List[float], company_id: int) -> Tuple[List[str], List[str]]:
    pipeline = [
        {"$vectorSearch": {
            "index": "ai_responses_vector_index",
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": 15, "limit": 5,
            "filter": {"company_id": company_id} 
        }},
        {"$project": {"_id": 1, "canonical_prompt": 1, "response": 1, "status": 1}}
    ]
    cursor = await ai_response_col.aggregate(pipeline) 
    results = await cursor.to_list(length=20) #type: ignore
    if not results: return [], [] # type: ignore

    memory_map = {m["canonical_prompt"]: m for m in results}


    def _find_similarities():
        if torch.cuda.is_available():
            torch.cuda.set_device(0)

        return find_similarities(query, list(memory_map.keys()), top_n=2)

    hits = await asyncio.to_thread(_find_similarities)
    
    sections = []
    used_ids = []
    for hit in hits:
        m = memory_map.get(hit)
        used_ids.append(str(m["_id"]))  # type: ignore
        label = {
            "canonical": "Verified Good Answer",
            "quarantine": "AVOID THIS - INCORRECT PREVIOUS ANSWER"
        }.get(m["status"], "Previous Draft Answer") # type: ignore
        
        sections.append(f"[{label}]: {m['response']}") # type: ignore
    return sections, used_ids


# Document Retrieval
async def fetch_document_context(query: str, query_vector: List[float], company_id: int) -> Tuple[List[str], List[str]]:
    pipeline = [
        {"$vectorSearch": {
            "index": "docs_vector_index",
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": 25, "limit": 15,
            "filter": {"company_id": company_id} 
        }},
        {"$project": {"_id": 1, "content": 1}}
    ]
    cursor = await doc_chunk_col.aggregate(pipeline)
    results = await cursor.to_list(length=50)#type: ignore
    if not results: return [], [] # type: ignore

    chunk_map = {d["content"]: d for d in results}


    def _rerank_documents():
        if torch.cuda.is_available():
            torch.cuda.set_device(0)
        return rerank_documents(query, list(chunk_map.keys()), top_n=10)
    
    top_chunks = await asyncio.to_thread(_rerank_documents)

    sections = []
    used_chunk_ids = []
    for chunk in top_chunks:
        c = chunk_map.get(chunk)
        used_chunk_ids.append(str(c["_id"])) # type: ignore
        sections.append(f"[Document Knowledge]: {chunk}")
        
    return sections, used_chunk_ids

import time

# Main Pipeline
async def run_rag_pipeline(query: str, user_id: int, company_id: int):
    t0 = time.perf_counter()

    original_query = query
    search_query = query
    
    if count_tokens(query) > 500:
        search_query = await summarize(query)
    
    t1 = time.perf_counter()
    print(f"Summarization: {t1-t0:.2f}s")

    new_event = PromptEvent(
        prompt_text=original_query,
        user_id=user_id,
        company_id=company_id
    )
    event_id = await create_prompt_event(new_event)
    t2 = time.perf_counter()
    print(f"Create prompt event: {t2-t1:.2f}s")

    query_vector = await asyncio.to_thread(create_embedding, f"query: {search_query}")

    t3 = time.perf_counter()
    print(f"Embedding creation: {t3-t2:.2f}s")

    memory_task = fetch_memory_context(search_query, query_vector, company_id)
    docs_task = fetch_document_context(search_query, query_vector, company_id)
    
    (memory_sections, memory_ids), (doc_sections, doc_ids) = await asyncio.gather(
        memory_task, docs_task
    )
    t4 = time.perf_counter()
    print(f"Vector search + reranking: {t4-t3:.2f}s")

    all_context = memory_sections + doc_sections

    final_prompt = f"Context:\n{'\n\n'.join(all_context)}\n\nQuestion: {search_query}\nAnswer:"
    answer_text = await ask_llm(final_prompt) # type: ignore
    t5 = time.perf_counter()
    print(f"LLM call: {t5-t4:.2f}s")
    new_response = AIResponse(
        canonical_prompt=search_query,
        response=answer_text,
        embedding=query_vector,
        model=DEFAULT_MODEL,
        company_id=company_id,
        source_doc_ids=doc_ids
    )
    ai_res_id = await create_ai_response(new_response)

    all_related_ids = memory_ids + [str(ai_res_id)]
    
    await push_ai_response_to_event(event_id, all_related_ids)
    t6 = time.perf_counter()
    print(f"DB writes: {t6-t5:.2f}s")
    
    print(f"TOTAL: {t6-t0:.2f}s")

    return RAGResult(
        ai_response_id=str(ai_res_id),
        event_id=str(event_id),
        response_text=answer_text,
        model=DEFAULT_MODEL,
        feedback_required=True
    )