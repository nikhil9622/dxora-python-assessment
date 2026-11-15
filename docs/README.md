# Screenshots & logs

Add evidence of the running application here (the assignment asks for
screenshots or logs). Suggested captures:

1. `docs_swagger.png` — the interactive API docs at http://localhost:4000/docs
2. `response_live.png` — a real `POST /posting` response with at least one
   platform showing `status: success` and a working `posted_url`.
3. `terminal_run.png` — the uvicorn startup log.

A quick way to capture a response as a log file:

```bash
curl -s -X POST http://localhost:4000/posting \
  -H "Content-Type: application/json" \
  -d @samples/request.json | python -m json.tool | tee docs/response_live.txt
```
