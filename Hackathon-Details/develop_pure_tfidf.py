import os
import json
import time
import math
import collections
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def tokenize(text):
    # Lowercase and match alphabetic tokens of length >= 2
    return re.findall(r"\b[a-z]{2,}\b", text.lower())

def test_pure_tfidf():
    start_time = time.time()
    
    # 1. Define stop words
    stop_words = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 
        'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 
        'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 
        'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 
        'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 
        'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 
        'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 
        'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 
        'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
    }
    
    # 2. Define JD text
    jd_text = """
    Senior AI Engineer — Founding Team. Modern ML systems, embeddings, retrieval, ranking, LLMs, fine-tuning.
    embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5, or similar).
    vector databases or hybrid search infrastructure — Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS.
    designing evaluation frameworks for ranking systems — NDCG, MRR, MAP.
    Strong Python.
    """
    
    jd_tokens = [w for w in tokenize(jd_text) if w not in stop_words]
    jd_tf = collections.Counter(jd_tokens)
    
    # 3. Load candidate profiles
    cids = []
    doc_tfs = []
    df = collections.defaultdict(int)
    
    print("Loading candidate texts...")
    with open(os.path.join(PROJECT_ROOT, "Hackathon-Details", "candidates.jsonl"), "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            c = json.loads(line)
            cid = c["candidate_id"]
            
            prof = c["profile"]
            summary = prof.get("summary", "")
            headline = prof.get("headline", "")
            current_title = prof.get("current_title", "")
            skills_str = " ".join([s["name"] for s in c.get("skills", [])])
            
            combined_text = f"{current_title} {headline} {summary} {skills_str}"
            tokens = [w for w in tokenize(combined_text) if w not in stop_words]
            tf = collections.Counter(tokens)
            
            doc_tfs.append((cid, tf))
            cids.append(cid)
            
            # Update Document Frequency
            for word in tf.keys():
                df[word] += 1
                
            if idx >= 10000: # Test with 10k
                break
                
    N = len(doc_tfs)
    print(f"Loaded {N} candidates. Calculating IDF...")
    
    # Calculate IDF for vocabulary
    idf = {}
    for word, count in df.items():
        idf[word] = math.log(1.0 + (N / (1.0 + count)))
        
    # IDF for JD tokens
    jd_vector = {}
    jd_norm = 0.0
    for word, tf_val in jd_tf.items():
        if word in idf:
            weight = tf_val * idf[word]
            jd_vector[word] = weight
            jd_norm += weight * weight
    jd_norm = math.sqrt(jd_norm)
    
    # Compute Cosine Similarity for each candidate
    similarities = []
    for cid, tf in doc_tfs:
        dot_product = 0.0
        doc_norm = 0.0
        
        # Calculate doc norm
        for word, tf_val in tf.items():
            weight = tf_val * idf[word]
            doc_norm += weight * weight
            if word in jd_vector:
                dot_product += weight * jd_vector[word]
                
        doc_norm = math.sqrt(doc_norm)
        
        sim = 0.0
        if doc_norm > 0.0 and jd_norm > 0.0:
            sim = dot_product / (doc_norm * jd_norm)
            
        similarities.append((cid, sim))
        
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    print("\nTop 5 by pure Python TF-IDF Cosine Similarity:")
    for rank, (cid, sim) in enumerate(similarities[:5], 1):
        print(f"  {rank}. {cid} | Similarity: {sim:.4f}")
        
    print(f"\nCompleted in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    test_pure_tfidf()