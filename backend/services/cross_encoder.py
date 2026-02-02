import torch.nn as nn
from sentence_transformers import CrossEncoder
from typing import List


model = CrossEncoder(
    "./backend/ml_models/bge-reranker-v2-m3",
    activation_fn=nn.Sigmoid()
)

def get_relevant_content(query: str, docs: List[str], threshold: float, top_n: int = 5) -> List[str]:
    if not docs:
        return []

    pairs = [[query, doc] for doc in docs]
    scores = model.predict(pairs)

    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    
    return [doc for doc, score in ranked if score >= threshold][:top_n]


def rerank_documents(query: str, retrieved_docs: List[str], top_n=5) -> List[str]: 
    return get_relevant_content(query, retrieved_docs, threshold=0.25, top_n=top_n)

def find_similarities(query: str, stored_questions: List[str], top_n=5) -> List[str]:
    return get_relevant_content(query, stored_questions, threshold=0.70, top_n=top_n)

if __name__ == "__main__":
    # --- TEST 1: Memory Matching (High Threshold 0.70) ---
    print("--- Testing: Memory Matching (find_similarities) ---")
    
    # Imagine these are 'canonical_prompt' entries in your MongoDB
    past_questions = [
        "What is the remote work policy for engineers?",
        "How do I reset my corporate VPN password?",
        "Guidelines for handling sensitive government data."
    ]
    
    # Scenario A: Very close match (Should pass 0.70)
    user_query_1 = "remote working rules for engineering team"
    matches = find_similarities(user_query_1, past_questions)
    print(f"Query: {user_query_1} -> Matches: {matches}") 
    # Expectation: ['What is the remote work policy for engineers?']

    # Scenario B: Different topic (Should fail 0.70)
    user_query_2 = "How do I book a flight for a business trip?"
    matches = find_similarities(user_query_2, past_questions)
    print(f"Query: {user_query_2} -> Matches: {matches}\n")
    # Expectation: [] (Empty list because it doesn't meet the strict threshold)

    # --- TEST 2: RAG Reranking (Lower Threshold 0.30) ---
    print("--- Testing: RAG Reranking (rerank_documents) ---")
    
    # Imagine these are chunks of a technical PDF from your database
    retrieved_chunks = [
        "Section 5.1: The turbine safety seal must be inspected every 6 months.",
        "The employee cafeteria is open from 8 AM to 4 PM.",
        "The mechanical seal prevents leakage in high-pressure turbine environments.",
        "Annual leave must be requested 2 weeks in advance via the HR portal."
    ]
    
    # User is asking a technical question
    tech_query = "How often should I check the turbine seals?"
    
    relevant_context = rerank_documents(tech_query, retrieved_chunks)
    print(f"Query: {tech_query}")
    for i, doc in enumerate(relevant_context):
        print(f"  Rank {i+1}: {doc}")
    # Expectation: Both 'Section 5.1...' and 'The mechanical seal...' should appear.
    # The 'cafeteria' and 'annual leave' chunks should be filtered out.