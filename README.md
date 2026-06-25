# Intelligent Candidate Discovery & Ranking Engine

An ultra-fast, offline, and standard-library-only candidate matching and ranking pipeline built to process 100,000 candidate profiles. It identifies and ranks the top 100 matching candidates for a Senior AI/ML Engineer job description, fully hardening the pipeline against common resume loopholes and keyword stuffing.

---

## 🚀 Key Features

1. **Deterministic Anomaly Sieve**: Fully screens out 100% of synthetic honeypots and consulting firm candidates before scoring (detecting YoE-vs-calendar span mismatches, calendar-duration anomalies, and expert zero-duration profiles).
2. **Custom BM25 Relevance Engine**: Uses a standard-library implementation of the BM25 text retrieval algorithm ($k_1=1.2, b=0.75$) with term frequency saturation and document length normalization to neutralize keyword stuffers.
3. **Heuristic Feature Fusion**: Fuses multiple candidate signals including:
   - **Contextual Title Scoring**: Separates role seniority and domain components with a $0.3$ non-technical filter multiplier.
   - **Asymmetric Gaussian YoE Matching**: Centered around a target of 7.0 Years of Experience (YoE) to heavily penalize underqualified candidates while protecting senior candidates from overqualification penalties.
   - **Location & Work Mode Alignment**: Scores Noida/Pune hybrid constraints dynamically (with relocator and remote-preference logic).
4. **Skills Depth & Recency Decay**: Combines maximum depth of concept clusters rather than counts (to prevent generalist bias), applies natural logarithmic endorsement scaling, and uses exponential time-decay ($e^{-0.015 \cdot t}$) for older skill durations.
5. **SHA-256 Reasoner**: Employs a deterministic cryptographic hash seed of the candidate ID to guarantee rank-consistent, non-colliding reasoning sentences.
6. **Interactive Visualizer**: A lightweight, native web interface to inspect candidate rankings, profiles, and score breakdowns.

---

## 🛠️ Installation & Setup

### 1. Initialize Virtual Environment
Set up your Python virtual environment and install the required dependencies (used for PowerPoint generation and MCP setups):

```bash
# Clone the repository and navigate to root
cd intelligent-candidate-selection-hackathon

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

---

## 🏃 How to Run

### 1. Execute the Ranking Pipeline
The core ranking pipeline requires **zero external dependencies** and runs entirely on the Python Standard Library. To process the candidate profiles and output the final ranked CSV:

```bash
python rank.py --candidates ./Hackathon-Details/candidates.jsonl --out ./team_meta_minds.csv
```
*Note: This streams all 100,000 candidates in ~44 seconds using only ~16MB of active memory.*

### 2. Validate Submission Format
To verify that the output CSV meets the submission formatting rules:

```bash
python Hackathon-Details/validate_submission.py team_meta_minds.csv
```


### 3. Launch the Interactive Visualizer Dashboard
Start the local HTTP visualizer server to search, filter, and inspect ranked candidates:

```bash
python visualizer_server.py
```
Open `http://localhost:8000` in your web browser.

### 4. Generate PPTX Submission Presentation
To automatically compile and fill the submission PowerPoint deck:

```bash
python scratch/fill_ppt.py
```

### 5. Generate Editor MCP Server Configuration
If you want to configure your IDE to use the PPT MCP server on your device, run the following to automatically build the configuration file with your workspace paths:

```bash
python scratch/generate_mcp_config.py
```
