while true; do
  for i in {1..10}; do
    curl -s -o /dev/null http://localhost:8000/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{
        "model": "Qwen/Qwen3-30B-A3B-Instruct-2507",
        "messages": [{"role": "user", "content": "Database: formula_1. List all circuits."}],
        "max_tokens": 40
      }' &
  done
  sleep 0.1
done