# generate_embeddings.py
import pickle
from datasets import load_dataset
from sentence_transformers import SentenceTransformer

# 1. Load dataset
ds = load_dataset("its-myrto/fitness-question-answers")
questions = ds["train"]["Question"]
answers = ds["train"]["Answer"]

# 2. Build corpus
corpus = [f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)]

# 3. Embed corpus
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
corpus_embeddings = embedder.encode(corpus, convert_to_numpy=True)

# 4. Save to pickle
with open("fitness_corpus.pkl", "wb") as f:
    pickle.dump({"corpus": corpus, "embeddings": corpus_embeddings}, f)

print("Saved fitness_corpus.pkl with corpus + embeddings")
