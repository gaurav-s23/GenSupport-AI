import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

KB_DIR = "dataset/kb/"
FAISS_INDEX = "faiss_index.bin"

# Store text chunks to match vectors with text
documents = []


def load_knowledge_base():
    global documents

    text_chunks = []

    # Load text file
    product_file = os.path.join(KB_DIR, "product_info.txt")
    if os.path.exists(product_file):
        with open(product_file, "r", encoding="utf-8") as f:
            text_chunks += f.read().split("\n")

    # Load FAQ CSV
    faq_file = os.path.join(KB_DIR, "faq.csv")
    if os.path.exists(faq_file):
        data = pd.read_csv(faq_file)
        for _, row in data.iterrows():
            text_chunks.append(f"Q: {row['question']} A: {row['answer']}")

    documents = [chunk.strip() for chunk in text_chunks if chunk.strip()]


def create_faiss_index():
    if not documents:
        load_knowledge_base()

    embeddings = embedder.encode(documents)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))

    faiss.write_index(index, FAISS_INDEX)


def load_faiss_index():
    if not os.path.exists(FAISS_INDEX):
        create_faiss_index()
    return faiss.read_index(FAISS_INDEX)


def search_similar(query: str, top_k: int = 2):
    index = load_faiss_index()

    if not documents:
        load_knowledge_base()

    query_vec = embedder.encode([query]).astype("float32")
    distances, indices = index.search(query_vec, top_k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(documents):
            results.append(documents[idx])

    # fallback if no match found
    if not results:
        return ["We are reviewing this issue and will get back soon."]

    return results
