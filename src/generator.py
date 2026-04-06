# generator.py
# The ATTACKER — loads adversarial prompts and fires them at the RAG
# Saves every prompt + response to results/raw_responses.json

import json
import os
import sys
import time
from datetime import datetime

# Add the src directory to path so we can import the RAG pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from target_rag.finance_pipeline import initialize_pipeline, query_rag

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
PROMPTS_PATH   = "data/adversarial_prompts.json"
RESULTS_PATH   = "results/raw_responses.json"

# ─────────────────────────────────────────────
# STEP 1: Load adversarial prompts
# ─────────────────────────────────────────────
def load_prompts(path: str) -> list:
    """Load the 50 attack prompts from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    prompts = data["prompts"]
    print(f"[Attacker] Loaded {len(prompts)} adversarial prompts")
    return prompts

# ─────────────────────────────────────────────
# STEP 2: Fire all prompts at the RAG
# ─────────────────────────────────────────────
def run_attacks(prompts: list, rag_chain) -> list:
    """
    Send each prompt to the RAG pipeline and collect responses.
    Returns a list of result objects.
    """
    results = []
    total = len(prompts)

    print(f"\n[Attacker] Starting attack run — {total} prompts\n")
    print("=" * 60)

    for i, item in enumerate(prompts, start=1):
        prompt_id = item["id"]
        category  = item["category"]
        severity  = item["severity"]
        prompt    = item["prompt"]

        # Progress indicator
        print(f"[{i:02d}/{total}] {prompt_id} | {category.upper()} | severity: {severity}")
        print(f"         Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")

        # Fire the prompt at the RAG
        start_time = time.time()
        response   = query_rag(rag_chain, prompt)
        elapsed    = round(time.time() - start_time, 2)

        print(f"         Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        print(f"         Time: {elapsed}s\n")

        # Store the full result
        results.append({
            "id":        prompt_id,
            "category":  category,
            "severity":  severity,
            "prompt":    prompt,
            "response":  response,
            "elapsed_s": elapsed
        })

    print("=" * 60)
    print(f"[Attacker] Attack run complete — {total} responses collected")
    return results

# ─────────────────────────────────────────────
# STEP 3: Save results to JSON
# ─────────────────────────────────────────────
def save_results(results: list, path: str):
    """Save all prompt-response pairs to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    output = {
        "run_timestamp": datetime.now().isoformat(),
        "total_prompts": len(results),
        "results": results
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[Attacker] Results saved to {path}")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("   RAG-SHIELD — ATTACK RUN")
    print("=" * 60)

    # Initialize the RAG pipeline (target)
    print("\n[Attacker] Initializing RAG pipeline...")
    rag_chain = initialize_pipeline()

    # Load attack prompts
    prompts = load_prompts(PROMPTS_PATH)

    # Fire all attacks
    results = run_attacks(prompts, rag_chain)

    # Save raw responses
    save_results(results, RESULTS_PATH)

    print("\n[Attacker] Done. Raw responses ready for the Auditor.")
    print(f"           Check: {RESULTS_PATH}")
    