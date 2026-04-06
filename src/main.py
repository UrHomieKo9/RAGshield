# main.py
# RAG-Shield Orchestrator — runs the full red teaming pipeline in one command
# Usage: python src/main.py

import os
import sys
import json
import time
import subprocess
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(__file__))

from target_rag.finance_pipeline import initialize_pipeline, query_rag
from attacker.generator import load_prompts, run_attacks, save_results
from auditor.pii_scanner import scan_for_pii
from auditor.llm_judge import judge_response
from reporter.score import audit_all, calculate_score, save_report, print_summary
from langchain_community.llms import Ollama

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
PROMPTS_PATH      = "data/adversarial_prompts.json"
RAW_RESULTS_PATH  = "results/raw_responses.json"
FINAL_REPORT_PATH = "results/final_report.json"
OLLAMA_MODEL      = "phi3:mini"

# ─────────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────────
def print_banner():
    print("\n")
    print("██████╗  █████╗  ██████╗       ███████╗██╗  ██╗██╗███████╗██╗     ██████╗ ")
    print("██╔══██╗██╔══██╗██╔════╝       ██╔════╝██║  ██║██║██╔════╝██║     ██╔══██╗")
    print("██████╔╝███████║██║  ███╗█████╗███████╗███████║██║█████╗  ██║     ██║  ██║")
    print("██╔══██╗██╔══██║██║   ██║╚════╝╚════██║██╔══██║██║██╔══╝  ██║     ██║  ██║")
    print("██║  ██║██║  ██║╚██████╔╝       ███████║██║  ██║██║███████╗███████╗██████╔╝")
    print("╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝        ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝ ")
    print()
    print("           Automated Red Teaming Framework for RAG Pipelines")
    print("           Model: Phi-3 Mini  |  Vector Store: FAISS")
    print("           " + datetime.now().strftime("%d %B %Y · %H:%M:%S"))
    print()
    print("=" * 75)
    print()

# ─────────────────────────────────────────────
# STEP PRINTER
# ─────────────────────────────────────────────
def print_step(num, title):
    print(f"\n{'─' * 75}")
    print(f"  STEP {num} — {title.upper()}")
    print(f"{'─' * 75}\n")

def print_done(msg):
    print(f"\n  ✅  {msg}")

# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────
def run_pipeline():
    total_start = time.time()

    print_banner()

    # ── STEP 1: Initialize RAG
    print_step(1, "Initializing RAG Target")
    rag_chain = initialize_pipeline()
    print_done("RAG pipeline ready")

    # ── STEP 2: Load prompts
    print_step(2, "Loading Adversarial Prompts")
    prompts = load_prompts(PROMPTS_PATH)
    cats    = {}
    for p in prompts:
        cats[p["category"]] = cats.get(p["category"], 0) + 1
    for cat, count in cats.items():
        print(f"  • {cat:<15} {count} prompts")
    print_done(f"{len(prompts)} attack prompts loaded")

    # ── STEP 3: Run attacks
    print_step(3, "Running Attack Suite")
    raw_results = run_attacks(prompts, rag_chain)
    save_results(raw_results, RAW_RESULTS_PATH)
    print_done(f"All {len(raw_results)} attacks completed — responses saved")

    # ── STEP 4: Audit responses
    print_step(4, "Auditing Responses (PII Scanner + LLM Judge)")
    audited = audit_all(raw_results)

    # ── STEP 5: Score + report
    print_step(5, "Calculating Robustness Score")
    score = calculate_score(audited)
    save_report(score, audited, FINAL_REPORT_PATH)
    print_done(f"Final report saved to {FINAL_REPORT_PATH}")

    # ── Print summary
    print_summary(score)

    # ── Total time
    elapsed = round(time.time() - total_start, 1)
    print(f"\n  Total pipeline time: {elapsed}s")
    print(f"  Report timestamp:    {datetime.now().strftime('%d %b %Y · %H:%M:%S')}")
    print()

    return score

# ─────────────────────────────────────────────
# DASHBOARD LAUNCHER
# ─────────────────────────────────────────────
def offer_dashboard():
    print("=" * 75)
    print()
    answer = input("  Launch the Streamlit dashboard now? (y/n): ").strip().lower()
    if answer == "y":
        print("\n  Starting dashboard at http://localhost:8501 ...\n")
        subprocess.Popen(
            ["streamlit", "run", "dashboard/app.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("  ✅  Dashboard launched. Open http://localhost:8501 in your browser.")
        print("      (Press Ctrl+C in that terminal to stop it)\n")
    else:
        print("\n  Run manually anytime with:")
        print("      streamlit run dashboard/app.py\n")

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        score = run_pipeline()
        offer_dashboard()
    except KeyboardInterrupt:
        print("\n\n  Pipeline interrupted by user.\n")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"\n  ❌  File not found: {e}")
        print("      Make sure you're running from the project root:")
        print("      cd D:\\CURSOR FOLDER\\rag-shield")
        print("      python src/main.py\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ❌  Pipeline error: {e}")
        sys.exit(1)
        