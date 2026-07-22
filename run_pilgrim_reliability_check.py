import json
import time
from datetime import datetime
from pathlib import Path

from app.agents.orchestrator import process_message

TEST_SCENARIOS = [
    ("What time does Srisailam temple open?", ["5:30", "AM"]),
    ("How to reach Srisailam from Hyderabad?", ["Hyderabad"]),
    ("How to book darshan tickets?", ["srisailadevasthanam.org"]),
    ("Tell me about Rudrabhishekam seva", ["Rudrabhishekam"]),
    ("What prasadam is available at Srisailam?", ["prasadam"]),
    ("Where to stay in Srisailam?", ["Nandhiniketan", "accommodation"]),
    ("When is Maha Shivaratri celebration?", ["Shivaratri", "Feb"]),
    ("What is the significance of Srisailam temple?", ["Srisailam", "sacred"]),
    ("What documents needed for Srisailam darshan?", ["Aadhaar"]),
    ("How to avoid crowds at Srisailam?", ["morning", "crowd"]),
]

QUALITY_GATE_MIN_SCORE = 75


def run_checks():
    print("=" * 50)
    print("Srisailam Pilgrim Bot — Reliability Check")
    print("=" * 50)

    results = []

    for i, (message, must_contain) in enumerate(TEST_SCENARIOS):
        test_id = f"PILGRIM_TC_{i+1:03d}"
        phone = f"reliability_check_{i}"

        print(f"\nRunning {test_id}: {message}")
        try:
            response = process_message(message, phone)
            response_lower = response.lower()
            matched = any(keyword.lower() in response_lower for keyword in must_contain)
            score = 100 if matched else 30
            status = "passed" if matched else "failed"

            print(f"Result: {status} | Score: {score}")
            if not matched:
                print(f"Expected any of: {must_contain}")
                print(f"Got: {response[:200]}")

            results.append({
                "test_id": test_id,
                "message": message,
                "expected_keywords": must_contain,
                "response": response,
                "matched": matched,
                "score": score,
                "status": status,
            })
        except Exception as e:
            print(f"Result: failed | Error: {e}")
            results.append({
                "test_id": test_id,
                "message": message,
                "expected_keywords": must_contain,
                "response": None,
                "matched": False,
                "score": 0,
                "status": "failed",
                "error": str(e),
            })

        time.sleep(2)  # avoid rate limiting, same as the project's own tests

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = total - passed
    avg_score = sum(r["score"] for r in results) / total if total else 0
    quality_gate = "passed" if avg_score >= QUALITY_GATE_MIN_SCORE else "failed"

    summary = {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "average_score": round(avg_score, 1),
        "quality_gate": quality_gate,
    }

    print("\n" + "=" * 50)
    print("Test Run Completed")
    print("=" * 50)
    print(f"Total Tests  : {total}")
    print(f"Passed       : {passed}")
    print(f"Failed       : {failed}")
    print(f"Avg Score    : {summary['average_score']}")
    print(f"Quality Gate : {quality_gate.upper()}")

    report = {
        "generated_at": str(datetime.now()),
        "summary": summary,
        "results": results,
    }

    report_dir = Path("reports/json")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "latest_pilgrim_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"JSON Report  : {report_path}")

    return report


if __name__ == "__main__":
    run_checks()