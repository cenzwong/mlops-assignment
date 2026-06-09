for i in {1..10}
do
  echo "Executing request $i/10..."
  curl -X POST http://localhost:8001/answer \
    -H "Content-Type: application/json" \
    -d "{
      \"question\": \"Find the total number of races held in the year 200$i, schema verification run $i.\",
      \"db\": \"formula_1\",
      \"tags\": {
        \"experiment\": \"poc-baseline\",
        \"hardware\": \"1x-h100\",
        \"run_id\": \"phase4-loop-$i\"
      }
    }"
  sleep 1 
done