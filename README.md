# 🛡️ RAG-Shield

**Automated Red Teaming Framework for RAG Pipelines**

RAG-Shield is an end-to-end adversarial testing framework that automatically stress-tests Retrieval-Augmented Generation (RAG) pipelines. It generates adversarial attacks, evaluates the pipeline's defenses, and produces a quantified **RAG Robustness Index (RRI)** score — all locally, with no API costs.

Built as a flagship AI safety project to demonstrate real-world LLM security evaluation skills.

---

## 🔍 What It Does

Most RAG deployments are vulnerable to prompt injection, jailbreaks, and PII leakage — but few teams have a systematic way to measure this. RAG-Shield automates the full red teaming loop:

```
  ┌─────────────┐     50 adversarial     ┌─────────────┐
  │   ATTACKER  │ ──────────────────────▶│  RAG TARGET │
  │ (generator) │     prompts fired      │  (Phi-3 Mini│
  └─────────────┘                        │   + FAISS)  │
                                         └──────┬──────┘
                                                │ responses
                                                ▼
                                         ┌─────────────┐
                                         │   AUDITOR   │
                                         │ PII Scanner │
                                         │ + LLM Judge │
                                         └──────┬──────┘
                                                │ verdicts
                                                ▼
                                         ┌─────────────┐
                                         │  REPORTER   │
                                         │  RRI Score  │
                                         │  Dashboard  │
                                         └─────────────┘
```

---

## 📊 Key Finding — Before vs After

RAG-Shield identified critical vulnerabilities in Phi-3 Mini's default behavior and quantified the impact of prompt hardening:

| Metric | Before Hardening | After Hardening |
|---|---|---|
| **Overall RRI Score** | 44.0% | 78.0% |
| Jailbreak Resistance | 70.6% | 88.2% |
| Injection Resistance | 50.0% | 75.0% |
| PII Probe Resistance | 11.8% | 70.6% |

> PII probe attacks succeeded **88% of the time** on the default system prompt —  
> including leaking emails, phone numbers, and account IDs through innocent-sounding queries  
> with no jailbreak required.

---

## 🏗️ Architecture

```
rag-shield/
├── data/
│   ├── adversarial_prompts.json   # 50 curated attack prompts (3 categories)
│   └── sample_finance.csv         # Synthetic PII dataset for red teaming
│
├── src/
│   ├── attacker/
│   │   └── generator.py           # Fires all attacks, collects responses
│   ├── target_rag/
│   │   └── finance_pipeline.py    # LangChain + Ollama + FAISS RAG pipeline
│   ├── auditor/
│   │   ├── pii_scanner.py         # Regex-based PII leak detection
│   │   └── llm_judge.py           # LLM-as-a-Judge semantic safety scoring
│   ├── reporter/
│   │   └── score.py               # RRI calculation + report generation
│   └── main.py                    # Single-command pipeline orchestrator
│
├── dashboard/
│   └── app.py                     # Streamlit visual dashboard
│
├── results/
│   ├── raw_responses.json         # Raw attacker output
│   └── final_report.json          # Full scored audit report
│
├── Dockerfile
└── requirements.txt
```

---

## ⚔️ Attack Categories

RAG-Shield tests across 3 adversarial categories with 50 curated prompts:

| Category | Prompts | What It Tests |
|---|---|---|
| **Jailbreak** | 17 | Can the RAG be convinced to drop its safety rules? |
| **PII Probe** | 17 | Does the RAG leak emails, phones, or account numbers? |
| **Injection** | 16 | Can an attacker hijack the RAG's behavior via crafted input? |

Each prompt is tagged with severity (`high`, `medium`, `low`) and produces a `PASS` or `FAIL` verdict from two independent auditors.

---

## 🧪 Dual Auditor System

Every RAG response is evaluated by two independent layers:

**Layer 1 — PII Scanner (`pii_scanner.py`)**
Regex pattern matching for emails, phone numbers, account IDs, known account holder names, and balance amounts. Fast, deterministic, zero false negatives on structured PII.

**Layer 2 — LLM Judge (`llm_judge.py`)**
Phi-3 Mini acting as an independent safety evaluator. Catches semantic failures that regex misses — partial compliance, implicit data leakage, and instruction-following failures.

A response is marked `FAIL` if **either** auditor flags it.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- Phi-3 Mini pulled: `ollama pull phi3:mini`

### Installation

```bash
git clone https://github.com/UrHomieKo9/rag-shield
cd rag-shield
pip install -r requirements.txt
```

### Run the full pipeline

```bash
python src/main.py
```

This runs all 5 steps automatically:
1. Initializes the RAG pipeline and builds the FAISS index
2. Loads 50 adversarial prompts
3. Fires all attacks and collects responses
4. Audits each response (PII Scanner + LLM Judge)
5. Calculates the RRI score and launches the dashboard

### Run the dashboard only

```bash
streamlit run dashboard/app.py
```

### Docker

```bash
docker build -t rag-shield .

# Run the full pipeline
docker run rag-shield python src/main.py

# Launch dashboard
docker run -p 8501:8501 rag-shield
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM | Phi-3 Mini via Ollama (local inference) |
| RAG Framework | LangChain |
| Vector Store | FAISS |
| Embeddings | Ollama Embeddings |
| PII Detection | Python `re` (Regex) |
| LLM Judge | Phi-3 Mini (LLM-as-a-Judge pattern) |
| Dashboard | Streamlit + Plotly |
| Containerization | Docker |

---

## 💼 Applications

- **Enterprise AI Safety** — Test RAG systems before deploying them on sensitive internal data (HR, finance, legal)
- **Compliance Auditing** — Generate structured vulnerability reports for GDPR/SOC2 review
- **Model Benchmarking** — Compare robustness profiles across different LLMs on identical attack suites
- **Red Team Automation** — Replace manual prompt testing with a reproducible, scored pipeline

---

## 📁 Dataset

`data/adversarial_prompts.json` is a curated, categorized dataset of 50 adversarial prompts spanning jailbreaks, PII probes, and prompt injections. Released under CC-BY 4.0 for use in AI safety research and red teaming projects.

---

