import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from agent.graph import AgentState, graph

def main():
    # Let's test with California Schools
    state = AgentState(
        question="How many male clients in 'Hl.m. Praha' district?",
        db_id="financial"
    )
    print("Invoking graph...")
    try:
        res = graph.invoke(state)
        print("Success!")
        print("SQL:", res.get("sql"))
        print("Iteration:", res.get("iteration"))
        print("Verify OK:", res.get("verify_ok"))
        print("Verify Issue:", res.get("verify_issue"))
        print("History:")
        for h in res.get("history", []):
            print(" -", h)
    except Exception as e:
        print("Error during invoke:", e)

if __name__ == "__main__":
    main()
