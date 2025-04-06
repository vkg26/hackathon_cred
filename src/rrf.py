import numpy as np
import faiss
import pickle
import json
from client import client

def keyword_rank(query_keywords, candidates, top_k=5):
    scores = []
    for candidate in candidates:
        candidate_keywords = set(kw.lower() for kw in candidate.get("keywords", []))
        match_count = len(set(query_keywords).intersection(candidate_keywords))
        scores.append(match_count)
    top_indices = np.argsort(-np.array(scores))[:top_k]
    return top_indices

def embedding_rank(query_emb, index, top_k=5):
    D, I = index.search(np.array([query_emb]).astype("float32"), top_k)
    return I[0]

def reciprocal_rank_fusion(embed_ranks, keyword_ranks, k=60):
    fused_scores = {}
    for i, r in enumerate(embed_ranks):
        fused_scores[r] = fused_scores.get(r, 0) + 1 / (60 + i)
    for i, r in enumerate(keyword_ranks):
        fused_scores[r] = fused_scores.get(r, 0) + 1 / (60 + i)
    return sorted(fused_scores, key=fused_scores.get, reverse=True)

def get_best_match(query_text, query_embedding, query_keywords):
    # Load index + metadata
    index = faiss.read_index("data/faiss_index.faiss")
    with open("data/embeddings.pkl", "rb") as f:
        metadata = pickle.load(f)

    # Rank candidates
    embed_ranks = embedding_rank(query_embedding, index, top_k=5)
    keyword_ranks = keyword_rank(query_keywords, candidates=metadata, top_k=5)

    # Fuse rankings
    best_ids = reciprocal_rank_fusion(embed_ranks, keyword_ranks)
    best_match = metadata[best_ids[0]]
    return best_match

# extract_keywords_with_llm function to extract keywords from a query using LLM
def extract_keywords_with_llm(query, context_prompt=""):
    prompt = f"""
Given the following user query, extract the most relevant keywords.

Prior conversation context:
{context_prompt}

Query: "{query}"

Return the keywords as a comma-separated list.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts keywords."},
            {"role": "user", "content": prompt}
        ]
    )

    keywords_text = response.choices[0].message.content
    keywords = [kw.strip().lower() for kw in keywords_text.split(',') if kw.strip()]
    return keywords


