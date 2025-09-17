# rag_service/similarity.py
import pickle
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load model once
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

class SimilarityService:
    def __init__(self, embeddings_file=None):
        if embeddings_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            embeddings_file = os.path.join(base_dir, "utils", "corpus", "fitness_corpus.pkl")
        
        if not os.path.exists(embeddings_file):
            raise FileNotFoundError(f"{embeddings_file} not found. Run generate_embeddings.py first.")

        with open(embeddings_file, "rb") as f:
            data = pickle.load(f)

        self.corpus = data["corpus"]
        self.embeddings = data["embeddings"]

    def embed_query(self, query: str) -> np.ndarray:
        return embedder.encode([query], convert_to_numpy=True)[0]

    def get_corpus(self):
        return self.corpus, self.embeddings
        
    def check_domain_relevance(self, query: str, threshold: float = 0.65):
        """Check if query is relevant to fitness/health domain using cosine similarity"""
        query_embedding = self.embed_query(query)
        query_embedding = query_embedding.reshape(1, -1)  # Reshape for cosine_similarity
        
        # Compute cosine similarity with all embeddings
        sims = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get max similarity and its index
        max_sim = np.max(sims)
        best_idx = np.argmax(sims)
        
        print(f"Domain relevance score: {max_sim:.4f}, threshold: {threshold}")
        
        # Check threshold
        if max_sim >= threshold:
            return True, best_idx, max_sim
        else:
            return False, None, max_sim
