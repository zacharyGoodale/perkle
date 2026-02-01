# Testing Notes

This log captures the manual CSV workflow validation that was executed while investigating benefit-period detection.

## CSV workflow (manual)

```bash
cd backend && uv sync
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/auth/register -H 'Content-Type: application/json' -d '{"username":"tester","email":"tester@example.com","password":"TestPass123!"}'
curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"username":"tester","password":"TestPass123!"}'
curl -s http://localhost:8000/api/cards/available
curl -s -X POST http://localhost:8000/api/cards/my -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d "{\"card_config_id\":\"$CARD_ID\",\"nickname\":\"Gold\",\"card_anniversary\":null}"
curl -s -X POST http://localhost:8000/api/transactions/upload -H "Authorization: Bearer $TOKEN" -F "file=@/workspace/perkle/tmp_transactions.csv"
curl -s -X POST http://localhost:8000/api/benefits/detect -H "Authorization: Bearer $TOKEN"
```

## Auth session refresh workflow (manual)

```bash
cd backend && uv sync
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Register + login to get tokens
curl -s -X POST http://localhost:8000/api/auth/register \\
  -H 'Content-Type: application/json' \\
  -d '{"username":"sessiontester","email":"sessiontester@example.com","password":"TestPass123!"}'

TOKENS=$(curl -s -X POST http://localhost:8000/api/auth/login \\
  -H 'Content-Type: application/json' \\
  -d '{"username":"sessiontester","password":"TestPass123!"}')

ACCESS_TOKEN=$(echo "$TOKENS" | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$TOKENS" | jq -r '.refresh_token')

# Use refresh token to get a new access token
curl -s -X POST http://localhost:8000/api/auth/refresh \\
  -H 'Content-Type: application/json' \\
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}"

# Verify an authenticated endpoint still works with the access token
curl -s http://localhost:8000/api/cards/my -H "Authorization: Bearer $ACCESS_TOKEN"
```
