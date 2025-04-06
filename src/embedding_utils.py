import openai
import json
import numpy as np
import faiss
import os
from client import client

def generate_embedding(text, model="text-embedding-3-large"):
    response = client.embeddings.create(
        input=[text],
        model=model
    )
    return response.data[0].embedding

def build_vector_index(past_queries_path, save_dir):
    with open(past_queries_path, "r") as f:
        data = json.load(f)

    embeddings = []
    metadata = []

    for item in data:
        step_descriptions = " ".join([
            step.get("description", "") for step in item.get("steps", [])
        ])
        full_text = item["query"] + " " + step_descriptions
        emb = generate_embedding(full_text)
        embeddings.append(emb)
        metadata.append(item)

    # Save embeddings and metadata
    np_embeddings = np.array(embeddings).astype("float32")
    faiss_index = faiss.IndexFlatL2(np_embeddings.shape[1])
    faiss_index.add(np_embeddings)

    faiss.write_index(faiss_index, os.path.join(save_dir, "faiss_index.faiss"))

    with open(os.path.join(save_dir, "embeddings.pkl"), "wb") as f:
        import pickle
        pickle.dump(metadata, f)

    print(f"✅ Vector DB created with {len(data)} items.")

if __name__ == "__main__":
    build_vector_index("data/sample_queries.json", "data/")
