```
export $(cat .env | xargs)
```

git config --global user.name "Cenz Wong"
git config --global user.email "cenzth@gmail.com"


Phrase 3
- uv run uvicorn agent.server:app --host 0.0.0.0 --port 8001 --reload