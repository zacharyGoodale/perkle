# Testing Notes

This log captures the manual CSV workflow validation that was executed while investigating benefit-period detection.

## CSV workflow (manual)

```bash
cd backend && uv sync
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Use your HTTPS origin (required for Secure refresh cookies)
BASE_URL="https://<your-tailscale-hostname>:8443"
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

# Register + login (login sets HttpOnly refresh cookie and returns access token)
curl -sk -X POST "$BASE_URL/api/auth/register" \\
  -H 'Content-Type: application/json' \\
  -d '{"username":"sessiontester","email":"sessiontester@example.com","password":"TestPass123!"}'

TOKENS=$(curl -sk -X POST "$BASE_URL/api/auth/login" \\
  -H 'Content-Type: application/json' \\
  -d '{"username":"sessiontester","password":"TestPass123!"}')

ACCESS_TOKEN=$(echo "$TOKENS" | jq -r '.access_token')

# Use cookie jar for refresh flow
curl -sk -c cookies.txt -X POST "$BASE_URL/api/auth/login" \\
  -H 'Content-Type: application/json' \\
  -d '{"username":"sessiontester","password":"TestPass123!"}' > /tmp/tokens.json

curl -sk -b cookies.txt -c cookies.txt -X POST "$BASE_URL/api/auth/refresh"

# Verify an authenticated endpoint still works with the access token
curl -sk "$BASE_URL/api/cards/my" -H "Authorization: Bearer $ACCESS_TOKEN"
```
