import os
import json
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_tfidf():
    start_time = time.time()
    
    # Load candidate profiles (summary + current_title + skills)
    texts = []
    cids = []
    
    # We will only load the first 10,000 for a quick test
    print("Loading candidate texts...")
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            # Combine relevant fields
            prof = c["profile"]
            summary = prof.get("summary", "")
            headline = prof.get("headline", "")
            current_title = prof.get("current_title", "")
            skills_str = " ".join([s["name"] for s in c.get("skills", [])])
            
            combined_text = f"{current_title} {headline} {summary} {skills_str}"
            texts.append(combined_text)
            cids.append(cid)
            
            if idx >= 10000: # Test with 10k first
                break
                
    load_time = time.time() - start_time
    print(f"Loaded {len(texts)} texts in {load_time:.2f} seconds.")
    
    # Define Job Description text
    jd_text = """
    Senior AI Engineer — Founding Team. Modern ML systems, embeddings, retrieval, ranking, LLMs, fine-tuning.
     embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5, or similar).
    vector databases or hybrid search infrastructure — Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS.
    designing evaluation frameworks for ranking systems — NDCG, MRR, MAP.
    Strong Python.
    """
    
    # Run TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts + [jd_text])
    
    candidate_vectors = tfidf_matrix[:-1]
    jd_vector = tfidf_matrix[-1]
    
    similarities = cosine_similarity(candidate_vectors, jd_vector).flatten()
    
    # Sort and show top 5
    top_indices = similarities.argsort()[::-1][:5]
    print("\nTop 5 by TF-IDF Cosine Similarity:")
    for idx in top_indices:
        print(f"Candidate {cids[idx]} | Similarity: {similarities[idx]:.4f}")
        
    print(f"TF-IDF process completed in {time.time() - start_time:.2f} seconds total.")

if __name__ == "__main__":
    test_tfidf()