import faiss
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class Retriever:
    def __init__(self, corpus, embeddings):
        self.corpus = corpus
        self.embeddings = embeddings.astype("float32")

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.embeddings)

    def search(self, query_embedding, top_k=3, threshold=0.65):
        # Cosine similarity search with threshold
        query_embedding = query_embedding.reshape(1, -1)
        sims = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Sort by similarity and apply threshold
        indices = sims.argsort()[::-1]
        results = []
        
        for i, idx in enumerate(indices[:top_k]):
            if sims[idx] >= threshold:
                results.append(self.corpus[idx])
                print(f"Cosine match {i+1}: score={sims[idx]:.4f}")
            
        return results
        
