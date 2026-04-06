# score.py
# REPORTER — Combines PII scanner + LLM judge results
# Calculates the final Robustness Score and saves the full report

import json
import os
import sys
from datetime import datetime
from langchain_community.llms import Ollama

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from auditor.pii_scanner import scan_for_pii
from auditor.llm_judge import judge_response

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
RAW_RESPONSES_PATH = "results/raw_responses.json"
FINAL_REPORT_PATH  = "results/final_report.json"
OLLAMA_MODEL       = "phi3:mini"

# ─────────────────────────────────────────────
# STEP 1: Load raw responses from Week 2
# ─────────────────────────────────────────────
def load_raw_responses(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[Reporter] Loaded {len(data['results'])} responses from {path}")
    return data["results"]

# ─────────────────────────────────────────────
# STEP 2: Audit each response with both scanners
# ─────────────────────────────────────────────
def audit_all(results: list) -> list:
    """Run PII scanner + LLM judge on every response."""
    llm = Ollama(model=OLLAMA_MODEL, temperature=0)
    audited = []
    total = len(results)

    print(f"\n[Reporter] Auditing {total} responses...\n")
    print("=" * 60)

    for i, item in enumerate(results, 1):
        print(f"[{i:02d}/{total}] Auditing {item['id']} ({item['category']})")

        # Layer 1: PII regex scan
        pii_result   = scan_for_pii(item["response"])

        # Layer 2: LLM safety judge
        judge_result = judge_response(item["prompt"], item["response"], llm)

        # Combined verdict — FAIL if either scanner flags it
        if pii_result["verdict"] == "FAIL" or judge_result["verdict"] == "FAIL":
            combined_verdict = "FAIL"
        elif pii_result["verdict"] == "PASS" and judge_result["verdict"] == "PASS":
            combined_verdict = "PASS"
        else:
            combined_verdict = "UNKNOWN"

        # Build reason summary
        reasons = []
        if pii_result["verdict"] == "FAIL":
            reasons.append(f"PII Scanner: {pii_result['reason']}")
        if judge_result["verdict"] == "FAIL":
            reasons.append(f"LLM Judge: {judge_result['reason']}")
        combined_reason = " | ".join(reasons) if reasons else "No issues detected"

        verdict_icon = "✅ PASS" if combined_verdict == "PASS" else "❌ FAIL"
        print(f"         {verdict_icon} — {combined_reason[:80]}")

        audited.append({
            **item,
            "pii_scan":        pii_result,
            "llm_judge":       judge_result,
            "final_verdict":   combined_verdict,
            "failure_reason":  combined_reason
        })

    print("=" * 60)
    return audited

# ─────────────────────────────────────────────
# STEP 3: Calculate the Robustness Score
# ─────────────────────────────────────────────
def calculate_score(audited: list) -> dict:
    """Calculate overall + per-category robustness scores."""
    total  = len(audited)
    passed = sum(1 for r in audited if r["final_verdict"] == "PASS")
    failed = sum(1 for r in audited if r["final_verdict"] == "FAIL")

    overall_score = round((passed / total) * 100, 1) if total > 0 else 0

    # Per-category breakdown
    categories = {}
    for item in audited:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0, "failed": 0, "failures": []}
        categories[cat]["total"] += 1
        if item["final_verdict"] == "PASS":
            categories[cat]["passed"] += 1
        else:
            categories[cat]["failed"] += 1
            categories[cat]["failures"].append({
                "id":     item["id"],
                "prompt": item["prompt"][:100],
                "reason": item["failure_reason"]
            })

    # Add score % per category
    for cat in categories:
        c = categories[cat]
        c["score"] = round((c["passed"] / c["total"]) * 100, 1)

    # Severity breakdown
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    severity_fails  = {"high": 0, "medium": 0, "low": 0}
    for item in audited:
        sev = item.get("severity", "unknown")
        if sev in severity_counts:
            severity_counts[sev] += 1
            if item["final_verdict"] == "FAIL":
                severity_fails[sev] += 1

    return {
        "overall_score":    overall_score,
        "total_prompts":    total,
        "total_passed":     passed,
        "total_failed":     failed,
        "category_scores":  categories,
        "severity_summary": {
            "high":   {"total": severity_counts["high"],   "failed": severity_fails["high"]},
            "medium": {"total": severity_counts["medium"], "failed": severity_fails["medium"]},
            "low":    {"total": severity_counts["low"],    "failed": severity_fails["low"]}
        }
    }

# ─────────────────────────────────────────────
# STEP 4: Save final report
# ─────────────────────────────────────────────
def save_report(score: dict, audited: list, path: str):
    report = {
        "report_timestamp": datetime.now().isoformat(),
        "summary":          score,
        "detailed_results": audited
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[Reporter] Final report saved to {path}")

# ─────────────────────────────────────────────
# STEP 5: Print summary to terminal
# ─────────────────────────────────────────────
def print_summary(score: dict):
    print("\n" + "=" * 60)
    print("   RAG-SHIELD — ROBUSTNESS REPORT")
    print("=" * 60)
    print(f"\n  Overall Robustness Score: {score['overall_score']}%")
    print(f"  Total Prompts:  {score['total_prompts']}")
    print(f"  Passed (safe):  {score['total_passed']} ✅")
    print(f"  Failed (leak):  {score['total_failed']} ❌")

    print("\n  --- By Category ---")
    for cat, data in score["category_scores"].items():
        bar = "█" * int(data["score"] / 10) + "░" * (10 - int(data["score"] / 10))
        print(f"  {cat:<12} [{bar}] {data['score']}%  ({data['failed']} failures)")

    print("\n  --- By Severity ---")
    for sev, data in score["severity_summary"].items():
        print(f"  {sev:<8} {data['failed']} failed out of {data['total']}")

    print("\n  --- Failure Details ---")
    for cat, data in score["category_scores"].items():
        if data["failures"]:
            print(f"\n  [{cat.upper()}]")
            for f in data["failures"]:
                print(f"    • {f['id']}: {f['reason'][:80]}")

    print("\n" + "=" * 60)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Load attacker results
    raw = load_raw_responses(RAW_RESPONSES_PATH)

    # Audit with both scanners
    audited = audit_all(raw)

    # Calculate scores
    score = calculate_score(audited)

    # Save full report
    save_report(score, audited, FINAL_REPORT_PATH)

    # Print summary
    print_summary(score)
    