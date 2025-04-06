import os
import json
import numpy as np
import faiss
import pickle
from rrf import embedding_rank, keyword_rank, reciprocal_rank_fusion, extract_keywords_with_llm
from embedding_utils import generate_embedding
from client import client

# Paths for insight data
INDEX_PATH = "data/insights/insight_faiss_index.faiss"
METADATA_PATH = "data/insights/insight_metadata.pkl"

# Query the index using embedding + keyword fusion
def query_insights(user_query):
    index = faiss.read_index(INDEX_PATH)
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)

    query_emb = generate_embedding(user_query)
    query_keywords = extract_keywords_with_llm(user_query)

    embed_ranks = embedding_rank(query_emb, index, top_k=5)
    keyword_ranks = keyword_rank(query_keywords, metadata, top_k=5)
    top_ids = reciprocal_rank_fusion(embed_ranks, keyword_ranks)

    top_chunks = [metadata[i] for i in top_ids[:5]]
    return top_chunks

def answer_with_llm(user_query, top_chunks, context_prompt=""):
    context = "\n\n".join([c["text"] for c in top_chunks])
    prompt = f"""
You are an intelligent assistant that provides user insights from app data.

Prior conversation context:
{context_prompt}

User Query: "{user_query}"

Context:
{context}

Answer the user's query using only the information above.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful insights assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()


# CLI for querying only
def main():
    user_query = input("Enter your query: ")
    top_chunks = query_insights(user_query)
    answer = answer_with_llm(user_query, top_chunks)
    print("\nAnswer:\n", answer)

if __name__ == "__main__":
    main()
