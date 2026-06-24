"""
Evaluates classifier accuracy against the hand-labeled evaluation set.

This produces the metrics referenced in the Design & Testing Document
(category accuracy, priority accuracy, and a confusion breakdown), giving
the project a concrete, reproducible measure of classifier quality rather
than a subjective "it seems to work" claim.

Run with: python -m tests.eval_classifier
(requires a running Ollama instance with the configured model pulled)
"""
import json
import time
from collections import defaultdict

from app.services.classifier import classify_ticket


def _classify_with_retry(subject: str, body: str, retries: int = 3, backoff: float = 5.0):
    """Classify with retry/backoff so transient rate limits (HTTP 429) on a free
    hosted provider don't abort the run."""
    for attempt in range(retries):
        try:
            return classify_ticket(subject, body)
        except Exception as exc:
            if "429" in str(exc) and attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            raise


def run_evaluation(eval_path: str = "data/eval_set.json", delay: float = 1.5) -> dict:
    with open(eval_path) as f:
        eval_set = json.load(f)

    results = []
    category_correct = 0
    priority_correct = 0
    failures = []

    for ticket in eval_set:
        try:
            prediction = _classify_with_retry(ticket["subject"], ticket["body"])
        except Exception as exc:
            failures.append({"id": ticket["id"], "error": str(exc)})
            continue
        # Be polite to free-tier rate limits between requests.
        time.sleep(delay)

        cat_match = prediction.category.value == ticket["true_category"]
        pri_match = prediction.priority.value == ticket["true_priority"]

        category_correct += int(cat_match)
        priority_correct += int(pri_match)

        results.append({
            "id": ticket["id"],
            "subject": ticket["subject"],
            "true_category": ticket["true_category"],
            "predicted_category": prediction.category.value,
            "category_match": cat_match,
            "true_priority": ticket["true_priority"],
            "predicted_priority": prediction.priority.value,
            "priority_match": pri_match,
            "confidence": prediction.confidence,
        })

    n = len(results)
    summary = {
        "total_evaluated": n,
        "failures": len(failures),
        "category_accuracy": round(category_correct / n, 3) if n else 0,
        "priority_accuracy": round(priority_correct / n, 3) if n else 0,
        "results": results,
        "failure_details": failures,
    }
    return summary


def print_confusion_summary(results: list[dict], field: str):
    """Prints a simple per-class breakdown of correct vs incorrect predictions."""
    breakdown = defaultdict(lambda: {"correct": 0, "incorrect": 0})
    true_field = f"true_{field}"
    match_field = f"{field}_match"

    for r in results:
        key = r[true_field]
        if r[match_field]:
            breakdown[key]["correct"] += 1
        else:
            breakdown[key]["incorrect"] += 1

    print(f"\n--- {field.title()} breakdown ---")
    for cls, counts in sorted(breakdown.items()):
        total = counts["correct"] + counts["incorrect"]
        acc = counts["correct"] / total if total else 0
        print(f"  {cls:15s} accuracy: {acc:.2%}  ({counts['correct']}/{total})")


if __name__ == "__main__":
    summary = run_evaluation()

    print(f"Evaluated {summary['total_evaluated']} tickets ({summary['failures']} failures)")
    print(f"Category accuracy: {summary['category_accuracy']:.2%}")
    print(f"Priority accuracy:  {summary['priority_accuracy']:.2%}")

    print_confusion_summary(summary["results"], "category")
    print_confusion_summary(summary["results"], "priority")

    with open("tests/eval_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nFull results written to tests/eval_results.json")
