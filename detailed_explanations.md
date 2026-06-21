# Candidate Selection System — Technical Deep-Dive & Project Guide

This document provides detailed explanations of the core logic inside the candidate selection system, addresses specific ranking discrepancies, and outlines a step-by-step guide to run and iterate on the hackathon project.

---

## 1. Concept Clusters Diversification

### How Skills are Mismatched by Keyword Stuffers
Traditional candidate search tools count how many times keywords (e.g., "Pinecone", "Weaviate") appear. A candidate profile listing six different vector databases (e.g., Weaviate, Pinecone, Qdrant, Milvus, Faiss, Chroma) but nothing else would rank highly. However, a founding Senior AI Engineer needs a **broad skillset** that includes search retrieval, database indexing, model frameworks, and ranking evaluations.

### The Algorithm's Solution
The pipeline uses **Concept Clusters Diversification** to group technologies into four distinct clusters inside [rank.py](file:///c:/Users/Madhavi/Downloads/intelligent-candidate-selection-hackathon-main/intelligent-candidate-selection-hackathon-main/rank.py#L70-L86):

```python
CONCEPT_CLUSTERS = {
    "retrieval_search": {
        "embeddings", "retrieval", "dense_retrieval", "hybrid_search", 
        "vector_search", "information_retrieval", "search", "elasticsearch", 
        "opensearch", "bm25"
    },
    "vector_dbs": {
        "pinecone", "weaviate", "qdrant", "milvus", "faiss", "chroma", "vector_database"
    },
    "models_frameworks": {
        "sentence_transformers", "bert", "transformers", "pytorch", "tensorflow", 
        "huggingface", "llm", "llms", "gans", "yolo", "diffusion models", "rag", "fine_tuning"
    },
    "evaluation": {
        "ndcg", "mrr", "map", "evaluation", "offline evaluation", "ab_testing"
    }
}
```

### The Math Behind the Multiplier
A candidate's base skill score is calculated for matched skills. A **Cluster Diversity Multiplier** is then applied based on the number of unique clusters matched:

$$\text{Cluster Multiplier} = 0.40 + (\text{Matched Clusters} \times 0.15)$$

| Number of Unique Clusters Matched | Multiplier Calculation | Multiplier Value | Impact on Score |
| :---: | :---: | :---: | :--- |
| **1 Cluster** | $0.40 + (1 \times 0.15)$ | **0.55** | Decays score by 45% (narrow specialist) |
| **2 Clusters** | $0.40 + (2 \times 0.15)$ | **0.70** | Decays score by 30% |
| **3 Clusters** | $0.40 + (3 \times 0.15)$ | **0.85** | Decays score by 15% |
| **4 Clusters** | $0.40 + (4 \times 0.15)$ | **1.00** | Full score preserved (balanced engineer) |

This multiplier rewards candidates with experience across multiple areas and penalizes narrow specialization.

---

## 2. Deterministic, Variant Reasoning Generator

Generating natural-sounding justifications for 100 candidate matches without using external APIs or generating duplicate text is done using **deterministic pseudo-random selection**.

### The Seed Calculation
The generator derives a seed by summing the ASCII values of the candidate's unique ID:

$$\text{Seed} = \sum_{c \in \text{candidate\_id}} \text{ASCII}(c)$$

For example, candidate `"CAND_0001234"` will always produce the exact same seed value.

### Multi-Part Template Permutations
The justification string is divided into four sections:
1.  **Experience & Title Statement:** (3 templates) selected by `seed % len(exp_templates)`
2.  **Job Fit Statement:** (3 rank-dependent templates) selected by `(seed // 3) % len(fit_templates)`
3.  **Location Relocation Statement:** (3 local vs. relocation templates) selected by `(seed // 7) % len(loc_templates)`
4.  **Platform Availability/Notice Statement:** (3 templates) selected by `(seed // 11) % len(active_templates)`

### Structural Style Variations
To prevent identical sentence flow, the system randomly selects one of three structures using `seed % 3`:

*   **Style 0:** `[Experience] + [Fit] + [Location] + [Activity/Concern]`
*   **Style 1:** `[Fit] + [Experience] + [Location] + [Activity/Concern]`
*   **Style 2:** `[Experience] + [Location] + [Fit] + [Activity/Concern]`

This permutation-based generator yields $3 \times 3 \times 3 \times 3 \times 3 = 243$ unique combinations. It is 100% deterministic (yielding the same output for a given ID on every run) and executes instantly on the CPU.

---

## 3. TF-IDF (Term Frequency-Inverse Document Frequency)

**TF-IDF** evaluates how relevant a candidate’s profile text is to the target Job Description (JD).

```
Candidate Profile Text (Title + Headline + Summary + Skills)
                  │ Preprocess & Clean
                  ▼
          Term Frequency (TF)
                  │
                  ▼ Multiply
            TF-IDF Weight  ◄─── Inverse Document Frequency (IDF) [Corpus Rarity]
                  │
                  ▼ Cosine Similarity
           Similarity Score
```

### 1. Term Frequency (TF)
Counts how many times a normalized term $t$ appears in the candidate's profile text:

$$tf(t, d) = \text{Count of term } t \text{ in profile text } d$$

### 2. Inverse Document Frequency (IDF)
Measures the rarity of a term $t$ across the entire pool of $N$ qualified candidates:

$$idf(t, D) = \log\left(1.0 + \frac{N}{1.0 + \text{df}(t)}\right)$$

Where $\text{df}(t)$ is the number of candidate documents containing term $t$.
*   Common words (e.g., "software", "python") appear often, resulting in a low IDF score.
*   Unique terms (e.g., "weaviate", "ndcg") appear rarely, resulting in a higher IDF score.

### 3. Cosine Similarity
Calculates the cosine of the angle between the multi-dimensional vectors for the Job Description ($JD$) and the Candidate profile ($C$):

$$\text{Similarity}(JD, C) = \frac{JD \cdot C}{\|JD\| \|C\|} = \frac{\sum_{t} (w_{JD, t} \times w_{C, t})}{\sqrt{\sum_t (w_{JD, t})^2} \sqrt{\sum_t (w_{C, t})^2}}$$

Where $w_{i, t} = \text{tf}(t, i) \times \text{idf}(t)$. This value is then normalized against the highest similarity score in the dataset:

$$S_{\text{tfidf}} = \left( \frac{\text{Similarity}(JD, C)}{\text{Max Similarity}} \right) \times 100.0$$

---

## 4. How Technology Skills are Scored

Candidate skills are scored individually using endorsements and usage duration:

$$\text{Skill Score} = 10.0 \times \text{Proficiency Multiplier} \times \text{Endorsement Multiplier} \times \text{Duration Factor}$$

### 1. Proficiency Multiplier
Converts the experience level listed in the profile to a numerical weight:
*   `beginner`: $0.5$
*   `intermediate`: $0.8$
*   `advanced`: $1.0$
*   `expert`: $1.2$

### 2. Endorsement Multiplier
Rewards peer validation while capping extreme outliers:

$$\text{Endorsement Multiplier} = \min\left(1.5, 1.0 + \frac{\text{Endorsements}}{50.0}\right)$$

*   `0` endorsements = $1.0\times$ multiplier.
*   `25` endorsements = $1.5\times$ multiplier.
*   `50+` endorsements = $1.5\times$ max multiplier limit.

### 3. Duration Factor
Caps experience duration rewards to avoid biasing against younger platforms:

$$\text{Duration Factor} = \frac{\min(36.0, \text{Duration Months})}{12.0}$$

*   A skill used for $\le 3$ years scales linearly (e.g., 18 months = $1.5$ factor).
*   Any duration beyond 36 months is capped at a factor of $3.0$.

---

## 5. Candidate Ranking Discrepancies Explained

### Why a Candidate with 57% Response Rate Can Outrank a Candidate with 77% Response Rate

A candidate’s final rank is determined by their composite score, not by a single metric like recruiter response rate.

#### 1. The Recruiter Response Multiplier is Moderated
The response rate is converted to a multiplier using this formula:

$$M_{\text{response}} = 0.90 + (\text{Response Rate} \times 0.20)$$

*   For the **77% response rate** candidate:
    $$M_{\text{response}} = 0.90 + (0.77 \times 0.20) = 1.054$$
*   For the **57% response rate** candidate:
    $$M_{\text{response}} = 0.90 + (0.57 \times 0.20) = 1.014$$

The difference between the two multipliers is only **4%**. This small difference can be easily offset by other scoring criteria.

#### 2. Other Scoring Weights Have a Larger Impact
The main scoring weights range from 7% to 30% of the total score:

*   **Location Score (7% Weight):** Noida/Pune candidates receive 100 points. Candidates outside the region who are unwilling to relocate receive 30 points. This difference shifts the base score by **4.9 points** ($100 - 30 = 70 \times 0.07$).
*   **Experience Match (15% Weight):** Candidates in the 5–9 years range receive 100 points. Candidates outside this range receive 10 points. This shifts the base score by **13.5 points** ($90 \times 0.15$).
*   **Title Relevance (20% Weight):** A match with `GOOD_TITLES` receives 100 points, while other engineering titles receive 60 points. This shifts the base score by **8 points** ($40 \times 0.20$).
*   **TF-IDF Similarity (30% Weight):** Heavy lexical overlap shifts the base score by up to **27 points** compared to profiles with low keyword overlap.
*   **Concept Skill Clusters (20% Weight):** A broad technical background can shift the base score by up to **18 points** compared to a candidate with a narrow technical focus.

#### 3. Platform Inactivity Penalties
A high response rate candidate can be heavily penalized if they have not logged in recently:

*   Active within 30 days: **$1.10\times$ boost**
*   Inactive over 180 days: **$0.85\times$ penalty** (a 23% drop)

Even with a 77% response rate, a candidate will rank lower if they are based in a different location, have too much/little experience, have logged in inactive status, or lack core skill sets.

---

## 6. How to Start and Run the Project

Follow these steps to run the pipeline and validate your submission:

### Step 1: Environment Verification
Verify that Python 3.11.x is installed on your machine:
```bash
python --version
```

### Step 2: Extract the Candidate Dataset
Extract the compressed candidate pool file:
```bash
# On Linux / macOS:
gunzip -k Hackathon-Details/candidates.jsonl.gz

# On Windows:
# Extract using tools like 7-Zip, or let rank.py read candidates.jsonl directly once unzipped
```
Ensure that `candidates.jsonl` is saved in the `Hackathon-Details` directory.

### Step 3: Run the Main Ranking Pipeline
Execute [rank.py](file:///c:/Users/Madhavi/Downloads/intelligent-candidate-selection-hackathon-main/intelligent-candidate-selection-hackathon-main/rank.py) using the default configuration to process the data and generate your candidate selection list:
```bash
python rank.py --candidates ./Hackathon-Details/candidates.jsonl --out ./team_redrob.csv
```

### Step 4: Validate the Generated Output
Run the validation script on the generated CSV file to ensure it complies with the submission requirements:
```bash
python Hackathon-Details/validate_submission.py team_redrob.csv
```
*   If validation is successful, the terminal will print: `"Submission is valid."`
*   If the script flags any issues (such as incorrect row counts or sorting errors), fix them before submitting.

### Step 5: Update the Submission Metadata
Open [submission_metadata.yaml](file:///c:/Users/Madhavi/Downloads/intelligent-candidate-selection-hackathon-main/intelligent-candidate-selection-hackathon-main/submission_metadata.yaml) and update your team details, GitHub repository link, and sandbox hosted URL.
