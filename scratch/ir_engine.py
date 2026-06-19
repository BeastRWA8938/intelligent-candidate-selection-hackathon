import json
import time
import math
import collections
import re
from datetime import datetime

def get_stop_words():
    """Returns a set of standard English stop words used for IR tokenization."""
    return {
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

# Precompile the token pattern for speed
TOKEN_RE = re.compile(r"\b[a-z]{2,}\b")

def tokenize(text, stop_words=None):
    """
    Lowercases the text and extracts alphabetic tokens of length >= 2.
    Optionally filters out stop words if a stop words set is provided.
    """
    if not text:
        return []
    tokens = TOKEN_RE.findall(text.lower())
    if stop_words:
        return [w for w in tokens if w not in stop_words]
    return tokens


class TFIDFEngine:
    """
    A pure-Python TF-IDF Vector Space Model engine.
    Designed for high-performance and minimal memory footprint.
    """
    def __init__(self, stop_words=None):
        self.stop_words = stop_words if stop_words is not None else get_stop_words()
        self.idf = {}
        self.N = 0
        self.vocab = set()

    def tokenize(self, text):
        return tokenize(text, self.stop_words)

    def fit(self, doc_tfs):
        """
        Fits the global Document Frequency (DF) and calculates IDF.
        doc_tfs: iterable of collections.Counter (or dict of term -> count)
        """
        df = collections.defaultdict(int)
        self.N = 0
        
        for tf in doc_tfs:
            self.N += 1
            for word in tf.keys():
                df[word] += 1
                
        self.idf = {}
        # Apply standard smooth/regularized IDF formula matching the test baseline
        for word, count in df.items():
            self.idf[word] = math.log(1.0 + (self.N / (1.0 + count)))
        self.vocab = set(self.idf.keys())

    def get_query_vector(self, query_text):
        """
        Transforms a query string into a sparse TF-IDF vector {word: weight} and its norm.
        """
        query_tokens = self.tokenize(query_text)
        query_tf = collections.Counter(query_tokens)
        vector = {}
        norm_sq = 0.0
        for word, tf_val in query_tf.items():
            if word in self.idf:
                weight = tf_val * self.idf[word]
                vector[word] = weight
                norm_sq += weight * weight
        return vector, math.sqrt(norm_sq)

    def get_doc_vector_and_norm(self, doc_tf):
        """
        Transforms a doc TF Counter into a sparse TF-IDF vector {word: weight} and its norm.
        """
        vector = {}
        norm_sq = 0.0
        for word, tf_val in doc_tf.items():
            if word in self.idf:
                weight = tf_val * self.idf[word]
                vector[word] = weight
                norm_sq += weight * weight
        return vector, math.sqrt(norm_sq)

    def similarity(self, doc_tf, query_vector, query_norm):
        """
        Computes cosine similarity between a document TF Counter and a pre-calculated query vector.
        Optimized by evaluating dot product and document norm on the fly over non-zero terms.
        """
        dot_product = 0.0
        doc_norm_sq = 0.0
        
        # Compute doc norm and query intersection in a single loop over the doc's vocabulary
        for word, tf_val in doc_tf.items():
            if word in self.idf:
                weight = tf_val * self.idf[word]
                doc_norm_sq += weight * weight
                if word in query_vector:
                    dot_product += weight * query_vector[word]
                    
        doc_norm = math.sqrt(doc_norm_sq)
        if doc_norm > 0.0 and query_norm > 0.0:
            return dot_product / (doc_norm * query_norm)
        return 0.0


class ConceptClusterMatcher:
    """
    Implements multi-cluster skill intersection logic and synergy multipliers.
    Splits skills into 4 core clusters: retrieval, vector databases, models, and evaluation.
    """
    def __init__(self, clusters=None):
        if clusters is None:
            self.clusters = {
                "retrieval_search": {
                    "embeddings", "retrieval", "dense retrieval", "hybrid search", 
                    "vector search", "information retrieval", "search", "elasticsearch", 
                    "opensearch", "bm25"
                },
                "vector_dbs": {
                    "pinecone", "weaviate", "qdrant", "milvus", "faiss", "chroma"
                },
                "models_frameworks": {
                    "sentence-transformers", "bert", "transformers", "pytorch", 
                    "tensorflow", "huggingface", "llm", "llms", "gans", "yolo", 
                    "diffusion models", "rag"
                },
                "evaluation": {
                    "ndcg", "mrr", "map", "evaluation", "offline evaluation", "ab testing"
                }
            }
        else:
            self.clusters = {k: {w.lower().strip() for w in v} for k, v in clusters.items()}
            
        self.proficiency_map = {
            "beginner": 0.5,
            "intermediate": 0.8,
            "advanced": 1.0,
            "expert": 1.2
        }

    def match_candidate_skills(self, candidate_skills):
        """
        Calculates cluster overlap, weighted skills score, and synergy multiplier.
        
        candidate_skills: list of dicts, e.g. [{"name": "Milvus", "proficiency": "expert", "duration_months": 24}]
        Returns:
            dict with:
                - matched_clusters: number of active clusters matched (0-4)
                - cluster_multiplier: the computed multiplier (0.4 + matched_clusters * 0.15)
                - skills_weighted_score: sum of weighted score contributions of individual skills
                - concept_skill_score: final synergy score, capped at 100.0
                - matched_skills_by_cluster: dict of cluster -> list of matched skill names
                - all_matched_skills: list of all matched skill names
        """
        skills_weighted = 0.0
        matched_clusters = 0
        matched_skills_by_cluster = collections.defaultdict(list)
        all_matched_skills = []
        
        # Create a fast lookup dict for candidate skills
        skill_dict = {}
        for s in candidate_skills:
            if "name" in s:
                name_lower = s["name"].lower().strip()
                skill_dict[name_lower] = s

        # Check overlap for each cluster
        for cluster_name, keywords in self.clusters.items():
            overlap = set(skill_dict.keys()).intersection(keywords)
            if overlap:
                matched_clusters += 1
                for s_name in overlap:
                    s = skill_dict[s_name]
                    prof_level = s.get("proficiency", "beginner").lower().strip()
                    prof_mult = self.proficiency_map.get(prof_level, 0.5)
                    
                    dur = s.get("duration_months", 0)
                    if dur is None:
                        dur = 0
                        
                    end = s.get("endorsements", 0)
                    if end is None:
                        end = 0
                    end_mult = min(1.5, 1.0 + (end / 50.0))
                    
                    # Individual skill score component
                    s_score = 10.0 * prof_mult * end_mult * (min(36.0, dur) / 12.0)
                    skills_weighted += s_score
                    
                    matched_skills_by_cluster[cluster_name].append(s["name"])
                    all_matched_skills.append(s["name"])

        # Synergy multiplier formula
        # 1 cluster matched -> 0.55
        # 2 clusters matched -> 0.70
        # 3 clusters matched -> 0.85
        # 4 clusters matched -> 1.00
        cluster_mult = 0.4 + (matched_clusters * 0.15) if matched_clusters > 0 else 0.4
        
        # Scaling factor matching the benchmark model
        concept_skill_score = min(100.0, skills_weighted * cluster_mult * 3.0)

        return {
            "matched_clusters": matched_clusters,
            "cluster_multiplier": cluster_mult,
            "skills_weighted_score": skills_weighted,
            "concept_skill_score": concept_skill_score,
            "matched_skills_by_cluster": dict(matched_skills_by_cluster),
            "all_matched_skills": all_matched_skills
        }


def test_ir_engine(candidates_path, max_candidates=10000):
    """
    Test and benchmark the TF-IDF engine and Concept Cluster Matching.
    """
    print(f"--- Starting IR Engine Benchmark on {candidates_path} (limit={max_candidates}) ---")
    start_time = time.time()
    
    # Define sample JD text
    jd_text = """
    Senior AI Engineer — Founding Team. Modern ML systems, embeddings, retrieval, ranking, LLMs, fine-tuning.
    embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5, or similar).
    vector databases or hybrid search infrastructure — Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS.
    designing evaluation frameworks for ranking systems — NDCG, MRR, MAP.
    Strong Python.
    """
    
    stop_words = get_stop_words()
    engine = TFIDFEngine(stop_words)
    matcher = ConceptClusterMatcher()
    
    candidates = []
    doc_tfs = []
    
    print("Step 1: Loading candidate profiles and tokenizing texts...")
    load_start = time.time()
    
    # We load line by line for low memory overhead
    with open(candidates_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= max_candidates:
                break
            c = json.loads(line)
            
            # Combine fields for TF-IDF doc text
            prof = c["profile"]
            summary = prof.get("summary", "")
            headline = prof.get("headline", "")
            current_title = prof.get("current_title", "")
            skills_str = " ".join([s["name"] for s in c.get("skills", [])])
            
            combined_text = f"{current_title} {headline} {summary} {skills_str}"
            tokens = tokenize(combined_text, stop_words)
            tf = collections.Counter(tokens)
            
            candidates.append(c)
            doc_tfs.append(tf)
            
    load_time = time.time() - load_start
    print(f"Loaded and tokenized {len(candidates)} records in {load_time:.3f}s.")
    
    print("Step 2: Fitting TF-IDF Engine...")
    fit_start = time.time()
    engine.fit(doc_tfs)
    fit_time = time.time() - fit_start
    print(f"Fitted vocabulary size {len(engine.vocab)} in {fit_time:.3f}s.")
    
    print("Step 3: Calculating query vector...")
    q_vec, q_norm = engine.get_query_vector(jd_text)
    
    print("Step 4: Computing similarity scores & skill matching...")
    sim_start = time.time()
    
    results = []
    for i, c in enumerate(candidates):
        tf = doc_tfs[i]
        # TF-IDF Cosine Similarity
        sim = engine.similarity(tf, q_vec, q_norm)
        
        # Concept Cluster Match
        skills = c.get("skills", [])
        cluster_info = matcher.match_candidate_skills(skills)
        
        results.append({
            "candidate_id": c["candidate_id"],
            "similarity": sim,
            "concept_score": cluster_info["concept_skill_score"],
            "matched_clusters": cluster_info["matched_clusters"],
            "matched_skills": cluster_info["all_matched_skills"],
            "profile": c["profile"]
        })
        
    sim_time = time.time() - sim_start
    print(f"Calculated similarity & skill match for all candidates in {sim_time:.3f}s.")
    
    # Sort by Similarity descending
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    print("\nTop 5 Candidates by TF-IDF Similarity:")
    for rank, res in enumerate(results[:5], 1):
        print(f"  {rank}. {res['candidate_id']} | Sim: {res['similarity']:.4f} | Cluster Score: {res['concept_score']:.1f} ({res['matched_clusters']}/4 clusters)")
        print(f"     Title: {res['profile']['current_title']} | YoE: {res['profile']['years_of_experience']}y | Loc: {res['profile']['location']}")
        print(f"     Skills: {', '.join(res['matched_skills'][:6])}")
        
    total_time = time.time() - start_time
    print(f"\n--- Benchmark Completed in {total_time:.3f}s ---")
    print(f"Throughput: {len(candidates) / total_time:.1f} candidates/sec.")


if __name__ == "__main__":
    # Test on the candidate dataset
    test_ir_engine("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details/candidates.jsonl", max_candidates=10000)
