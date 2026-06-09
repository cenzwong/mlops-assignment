import json
import httpx
from pathlib import Path

AGENT_URL = "http://localhost:8001/answer"
EVAL_FILE = Path(__file__).resolve().parent.parent / "evals" / "eval_set.jsonl"

def main():
    if not EVAL_FILE.exists():
        print(f"Error: {EVAL_FILE} not found.")
        return

    with open(EVAL_FILE, "r") as f:
        questions = [json.loads(line) for line in f if line.strip()][:5]

    print(f"Loaded {len(questions)} test questions. Firing requests to {AGENT_URL}...\n")

    for i, q in enumerate(questions, 1):
        payload = {
            "question": q["question"],
            "db": q["db_id"]
        }
        print(f"[{i}/5] DB: {q['db_id']}")
        print(f"Question: {q['question']}")
        try:
            response = httpx.post(AGENT_URL, json=payload, timeout=60.0)
            if response.status_code == 200:
                res = response.json()
                print(f"Response OK: {res.get('ok')}")
                print(f"Final SQL: {res.get('sql')}")
                print(f"Iterations: {res.get('iterations')}")
                
                # Check if revision was triggered
                history = res.get("history", [])
                triggered_revise = any(h.get("node") == "revise" for h in history)
                print(f"Triggered Revise: {triggered_revise}")
                
                if triggered_revise:
                    print("History trace:")
                    for idx, step in enumerate(history):
                        node = step.get("node")
                        if node == "generate_sql":
                            print(f"  {idx}. generate_sql -> {step.get('sql')}")
                        elif node == "verify":
                            print(f"  {idx}. verify -> ok={step.get('verify_ok')}, issue={step.get('verify_issue')}")
                        elif node == "revise":
                            print(f"  {idx}. revise -> {step.get('sql')}")
            else:
                print(f"Error status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")
        print("-" * 60 + "\n")

if __name__ == "__main__":
    main()
