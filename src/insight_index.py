import json
import numpy as np
import faiss
import pickle
from embedding_utils import generate_embedding

CHUNKS_PATH = "data/insights/cred_user_data.json"
INDEX_PATH = "data/insights/insight_faiss_index.faiss"
METADATA_PATH = "data/insights/insight_metadata.pkl"

def build_insight_index():
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    embeddings = []
    metadata = []

    for chunk in chunks:
        emb = generate_embedding(chunk["text"])
        embeddings.append(emb)
        metadata.append(chunk)

    np_embeddings = np.array(embeddings).astype("float32")
    index = faiss.IndexFlatL2(np_embeddings.shape[1])
    index.add(np_embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print(f"✅ Built insight FAISS index with {len(metadata)} chunks.")

if __name__ == "__main__":
    build_insight_index()
