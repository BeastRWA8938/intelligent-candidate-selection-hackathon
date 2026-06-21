# Resume Ranking System – Loopholes and Failure Cases Analysis

## 1. Seed Generation

### Formula

\[
\text{Seed} = \sum_{i=1}^{n} \text{ASCII}(c_i)
\]

where:

- \(c_i\) = ith character of candidate ID
- \(n\) = number of characters in candidate ID

### Loopholes

#### 1.1 Collision Problem

Different candidate IDs can produce the same seed.

Example:

```
ABC
```

\[
65+66+67=198
\]

and

```
CAB
```

\[
67+65+66=198
\]

Same seed despite different IDs.

---

#### 1.2 Weak Randomization

Small changes in candidate IDs produce highly predictable changes in seed values.

Example:

```
ABC123
```

vs

```
ABC124
```

Only differs by ASCII(3) and ASCII(4).

---

#### 1.3 Order Information Loss

ASCII summation ignores character order.

```
ABCD
```

and

```
DCBA
```

produce identical seeds.

---

## 2. TF-IDF and Cosine Similarity

### Purpose

Used to compare job descriptions and resumes based on textual similarity.

---

## TF-IDF Failure Cases

### 2.1 Synonym Problem

JD:

```
Machine Learning
```

Resume:

```
Artificial Intelligence
```

Meaning is similar but words differ.

Low score.

---

### 2.2 Different Terminology

JD:

```
Large Language Models
```

Resume:

```
GPT-4
Claude
Llama
```

Human sees strong match.

TF-IDF sees weak overlap.

---

### 2.3 Expertise Not Measured

Candidate A:

```
Python
```

mentioned once.

Candidate B:

```
5 years Python
20 Python projects
```

TF-IDF cannot accurately capture expertise level.

---

### 2.4 Keyword Stuffing

Candidate repeats:

```
Python Python Python Python Python
```

Many times.

TF increases artificially.

---

### 2.5 Emerging Technology Bias

Rare skills receive high IDF.

Rare does not necessarily mean relevant.

---

## Cosine Similarity Failure Cases

### 2.6 Negation Failure

Resume:

```
No experience in NLP
```

Cosine still sees:

```
NLP
```

and increases similarity.

---

### 2.7 Context Ignorance

Resume A:

```
Studied TensorFlow in college assignment
```

Resume B:

```
Built TensorFlow systems serving 1 million users
```

Similar words.

Very different expertise.

---

### 2.8 Semantic Failure

JD:

```
Computer Vision
```

Resume:

```
Object Detection
Image Classification
Segmentation
```

Low overlap despite high relevance.

---

### 2.9 Leadership Ignorance

Candidate with:

- AI team leadership
- Publications
- Production deployments

may receive score similar to someone with only keyword matches.

---

## 3. Technology Skill Scoring

### Formula

\[
\text{Skill Score}
=
10
\times
\text{Proficiency Multiplier}
\times
\text{Endorsement Multiplier}
\times
\text{Duration Factor}
\]

---

### 3.1 Self-Declared Proficiency Bias

Candidate can simply choose:

```
Expert
```

without verification.

---

### 3.2 Endorsement Farming

Friends and colleagues can artificially increase endorsements.

Popularity ≠ skill.

---

### 3.3 Duration ≠ Competence

Candidate:

- 6 months intensive AI development

may lose to

- 3 years casual usage

due to duration multiplier.

---

### 3.4 Old Skill Advantage

Longer duration always wins.

May favor outdated technologies.

---

### 3.5 Skill Inflation

Candidate can mark many skills as:

```
Expert
```

without validation.

---

### 3.6 Fresh Graduate Penalty

New graduates naturally have lower duration.

Strong talent may score poorly.

---

### 3.7 Endorsement Saturation

25 endorsements:

\[
1.5
\]

500 endorsements:

\[
1.5
\]

Same score despite large difference.

---

### 3.8 Multiplication Amplification

Small differences in inputs become large score differences.

---

### 3.9 Irrelevant Skill Dominance

Candidate can accumulate high scores through irrelevant skills.

Example:

```
FORTRAN
COBOL
Visual Basic
```

may contribute heavily despite AI role.

---

### 3.10 No Recency Awareness

Skill last used in 2018 can still score highly.

---

### 3.11 Missing Semantic Relationships

Candidate knows:

```
GPT-4
LangChain
Claude
RAG
```

System may not infer:

```
LLM Expertise
```

---

### 3.12 Actual Competence Not Measured

Formula evaluates:

- Duration
- Endorsements
- Self-rating

It does not evaluate:

- Project quality
- Research
- Production impact

---

## 4. Recruiter Response Rate

### Formula

\[
M_{\text{response}}
=
0.90 + (\text{Response Rate}\times0.20)
\]

---

### 4.1 Small Sample Bias

Candidate:

- 1 recruiter contact
- 1 response

Response Rate:

\[
100\%
\]

Scores higher than candidates with hundreds of interactions.

---

### 4.2 Industry Bias

Different industries naturally have different response rates.

---

### 4.3 LinkedIn Premium Bias

Visibility can influence response rate.

Not necessarily skill.

---

### 4.4 Geography Bias

Major tech cities receive more recruiter attention.

---

### 4.5 Historical Bias

Old recruiter interactions may still influence score.

---

## 5. Location Score

### Weight

7%

---

### 5.1 Geography Bias

Strong candidate outside target city loses points.

---

### 5.2 Remote Work Ignored

Location may matter less for remote roles.

Yet system still penalizes.

---

## 6. Experience Match

### Weight

15%

---

### 6.1 Hard Cutoff Problem

Candidate:

```
4.9 years
```

gets drastically lower score than:

```
5.0 years
```

---

### 6.2 Overqualified Candidate Penalty

15-year candidate may be treated similarly to fresher.

---

## 7. Title Relevance

### Weight

20%

---

### 7.1 Job Title Bias

```
Data Scientist
```

may be equivalent to:

```
AI Engineer
```

but receives lower score.

---

### 7.2 Startup Title Penalty

Titles such as:

- Research Engineer
- Applied Scientist
- Founding Engineer

may be unfairly penalized.

---

## 8. TF-IDF Similarity Weight

### Weight

30%

---

### 8.1 Keyword Stuffing

Repeated keywords can inflate score.

---

### 8.2 Semantic Understanding Failure

System fails to connect:

```
LLM
```

with

```
GPT-4
Claude
Llama
```

---

### 8.3 Emerging Technology Mismatch

Modern tools may not match JD wording.

---

## 9. Concept Skill Clusters

### Weight

20%

---

### 9.1 Breadth Over Depth Bias

Generalists may outperform specialists.

---

### 9.2 Jack-of-All-Trades Effect

Candidate touching many domains receives higher score than deep expert.

---

### 9.3 Specialist Penalty

Strong AI researcher may lose to broad technology profile.

---

## 10. Combined System-Level Issues

### 10.1 Metadata Dominance

Large portions of score depend on:

- Location
- Title
- Experience

instead of actual capability.

---

### 10.2 Achievement Blindness

System ignores:

- Research papers
- Open-source contributions
- Hackathon wins
- Patents
- Production impact
- Leadership

---

### 10.3 Semantic Understanding Limitation

Heavy dependence on exact keywords.

Modern NLP embeddings would perform better.

---

### 10.4 Gaming the System

Candidates can manipulate:

- Keywords
- Endorsements
- Titles
- Skill declarations

to improve ranking without improving competence.

---

## Conclusion

The system is:

- Interpretable
- Explainable
- Easy to implement

However, it is vulnerable to:

- Keyword manipulation
- Self-reporting bias
- Geography bias
- Experience threshold effects
- Semantic understanding limitations
- Breadth-over-depth preference

Future improvements should incorporate:

- Transformer embeddings (BERT/Sentence-BERT)
- Semantic skill matching
- Project impact scoring
- GitHub analysis
- Research/publication metrics
- Certification validation
- Achievement-based ranking