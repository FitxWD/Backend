from fastapi import HTTPException
from .similarity import SimilarityService
from .retrieval import Retriever
from .llm import get_language_model_service
from ddgs import DDGS

# Global singleton instance
_rag_service_instance = None

class RAGService:
    def __init__(self, threshold: float = 0.3):
        # Load dataset embeddings
        self.similarity = SimilarityService()
        corpus, embeddings = self.similarity.get_corpus()

        # Init retriever + Gemini
        self.retriever = Retriever(corpus, embeddings)
        self.llm = get_language_model_service()
        self.threshold = threshold

    def hybrid_rag_answer(self, query: str, top_k: int = 3) -> dict:
        # 0. Check if query is in fitness/health domain
        in_domain, best_idx, sim_score = self.similarity.check_domain_relevance(
            query, threshold=self.threshold
        )
        
        if not in_domain:
            return {
                "answer": "Sorry, I can only answer fitness and health-related questions.",
                "source": "none",
                "results": []
            }
            
        # 1. Embed query
        query_embedding = self.similarity.embed_query(query)

        # 2. Retrieve from dataset
        results = self.retriever.search(query_embedding, top_k=top_k)

        if results:
            context = "\n".join(results)
            answer = self.llm.generate_answer(query=query, context=context)
            return {"answer": answer, "source": "Knowledge Base", "results": results}

        # 3. Web fallback
        web_results, urls = [], []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=top_k):
                web_results.append(r["body"])
                urls.append(r["href"])

        if web_results:
            context = "\n".join(web_results)
            # Format source for Gemini - pass URLs as context/source for reference
            answer = self.llm.generate_answer(query=query, context=context)
            return {"answer": answer, "source": urls, "results": web_results}

        # 4. Nothing found (should rarely get here due to domain check)
        return {
            "answer": "I don't have enough information to answer that fitness question.",
            "source": "none", 
            "results": []
        }

# Singleton getter function
def get_rag_service():
    global _rag_service_instance
    try:
        if _rag_service_instance is None:
            llm_service = get_language_model_service()

            if not llm_service.is_available():
                raise HTTPException(status_code=500, detail="Language model in rag service not available")
            # Create RAG service
            _rag_service_instance = RAGService()
    except Exception as e:
        print(f"Error initializing RAG service: {e}")
        raise HTTPException(status_code=500, detail="RAG service initialization failed")
    return _rag_service_instance
