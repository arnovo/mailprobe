# Mailprobe

Production-ready product: find and verify B2B emails, multi-tenant, integrated with **n8n** (webhooks, stable API, API Keys, idempotency). Spain/GDPR compliant (LOPDGDD).

**Stack:** Backend Python + FastAPI, PostgreSQL, Celery + Redis, Frontend Next.js (TypeScript). Deploy: Docker Compose local; easy on Render/Fly/DigitalOcean/Kubernetes.

---

## Requirements

- Docker and Docker Compose
- (Optional for local dev) Python 3.12+, Node 20+

---

## External Services and Potential Costs

This project **does not use paid APIs** for core logic (finding/verifying emails). The only "external services" are infrastructure and, optionally, billing.

| Service | Usage | Cost |
|---------|-------|------|
| **PostgreSQL** | Database (leads, users, jobs, etc.) | **Managed:** Render ~€7/month, Fly.io ~€5/month, Neon/Supabase free tier. **Self-hosted:** €0 if you have a server. |
| **Redis** | Celery queue (jobs, webhooks) | **Managed:** Upstash free tier (10k commands/day), Redis Cloud free. **Self-hosted:** €0. |
| **DNS (MX lookup)** | MX resolution for verification | **System resolver** (`dnspython` lib). No paid API (Google DNS, etc.). **€0**. |
| **SMTP (probe)** | Connection to MX servers of domains you verify (Gmail, O365, etc.) | **We don't send email.** We only do RCPT TO to *their* servers. **€0** (no SendGrid, SES, etc.). **Note:** In many environments (Docker, cloud) **port 25** is blocked or limited; SMTP verification may fail or timeout. Configurable timeout: `SMTP_TIMEOUT_SECONDS` (default 5). |
| **Web search (optional)** | Check if email appears on public pages | **Optional (configurable per workspace).** If MX doesn't respond (firewall, Barracuda...) we search if the email appears on the web. Providers: **Serper.dev** (Google, 2500/month free) or **Bing** (deprecated August 2025). Configure in **Dashboard → Config**. |
| **Outbound webhooks** | HTTP calls to your URLs (n8n, etc.) | **€0** (only outbound traffic from your server). |
| **Stripe** | Billing (paid plans) | **Only if you integrate it.** Model ready in DB (`stripe_customer_id`, etc.) but not implemented. Stripe charges ~1.5% + €0.25 per transaction. |

**Summary:**
- **Local / self-hosted:** €0 external services cost (only your machine/server).
- **Managed deploy (Render/Fly/DO):** typical cost **~€5–15/month** (Postgres + Redis + 1–2 instances).
- **No verification cost:** no external "email verification API" provider (ZeroBounce, NeverBounce, etc.); verification is built-in (MX + SMTP probe). Optionally you can add web search (Serper.dev or Bing) to check if email appears in public sources; each workspace configures it with its own API key in **Dashboard → Config**.

---

## SMTP-less Verification (environments with port 25 blocked)

Port 25 (SMTP) is blocked in many environments:
- **Docker Desktop (macOS/Windows):** Port 25 outbound is filtered.
- **Cloud providers:** AWS, GCP, Azure block or limit port 25 by default.
- **Residential ISPs:** Many block port 25 to prevent spam.

### Automatic Detection

The system automatically detects when SMTP is blocked:
- If there are timeouts to 3+ distinct MX servers in 5 minutes, the `smtp_blocked` flag is activated.
- The flag is stored in Redis with a 15-minute TTL.
- While active, verifications **do not attempt SMTP probes** (saves time and resources).

### Alternative Signals

When SMTP is unavailable, the verifier uses alternative signals:

| Signal | Description | Points |
|--------|-------------|--------|
| **MX** | MX records found | +20 |
| **SPF** | SPF record configured | +10 |
| **DMARC** | DMARC policy configured | +10 |
| **Provider** | Known provider (Google, Microsoft, etc.) | +10 |
| **Web** | Email found in public sources | +15 |

### Verification Statuses

| Status | Meaning |
|--------|---------|
| `valid` | SMTP confirmed the mailbox exists (only if SMTP available) |
| `risky` | Positive signals (MX, SPF, DMARC) but no SMTP confirmation |
| `unknown` | SMTP available but inconclusive response (real greylist) |
| `invalid` | Bad format, disposable domain, no MX, or SMTP rejected (550) |

### API Fields

The verification response includes detailed signals:

```json
{
  "best_result": {
    "email": "john.smith@company.com",
    "status": "risky",
    "confidence_score": 75,
    "mx_found": true,
    "spf_present": true,
    "dmarc_present": true,
    "catch_all": null,
    "smtp_attempted": false,
    "smtp_blocked": true,
    "provider": "google",
    "web_mentioned": false,
    "signals": ["mx", "spf", "dmarc", "provider:google", "smtp_blocked"],
    "reason": "MX ok | SPF | DMARC | provider:google | SMTP blocked"
  }
}
```

### Production Recommendation

For full SMTP verification, deploy the worker on a VPS with port 25 open (OVH, Hetzner, DigitalOcean in regions that allow it). The backend/API can remain in a cloud with port 25 blocked; only the Celery worker needs access.

---

## Local Setup (Docker Compose)

```bash
# Clone / enter the repo
cd mailprobe

# Copy env
cp backend/.env.example backend/.env
# Adjust JWT_SECRET_KEY and others if needed

# Start services
docker compose up -d

# Migrations
docker compose run --rm backend alembic -c alembic.ini upgrade head

# Create workspace and admin user (replace email)
docker compose run --rm backend python -m scripts.create_workspace --email admin@example.com --password changeme --workspace-name "My Company" --workspace-slug default
```

- **Backend API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3001

### View frontend changes without rebuilding

Only **one** frontend should be active. With the dev compose, **backend, frontend, worker and beat** use code mounting and hot reload (no rebuild needed).

| Port | When | What |
|------|------|------|
| **3001** | `docker compose up -d` (without dev) | **Production** frontend: fixed build, no hot reload. |
| **3002** | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` | **Development** frontend: mounted code, `npm run dev`, hot reload. Backend with `uvicorn --reload`. Worker and beat with `watchmedo` (restart on `.py` changes). |

If you have both running, to keep only development: `docker compose stop frontend` then `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d frontend`. To return to production: stop dev and `docker compose up -d frontend`.

**Option A — All in Docker with hot reload**

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

- **Backend:** mounts `./backend` and runs `uvicorn --reload`; Python changes reload automatically.
- **Worker and beat:** use the same backend image (with `watchdog`), mount `./backend` and run `watchmedo auto-restart`; they restart on any `.py` change. Only need to build once: `docker compose build backend`.
- **Frontend:** mounts `./frontend`, runs `npm run dev`; Next.js reloads on edits. Exposed at **http://localhost:3002**.

**Option B — Frontend locally**

```bash
cd frontend
npm install
npm run dev
```

Backend, Postgres and Redis stay in Docker; frontend at http://localhost:3001 uses API at http://localhost:8000.

---

## Create API Key (for n8n)

1. Log in to the frontend (or use `POST /v1/auth/login`).
2. With the token, create API key (or use endpoint if exposed in UI):

```bash
# Login
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme"}' | jq .

# Create API Key (use access_token and X-Workspace-Id from workspace returned by create_workspace, e.g. 1)
curl -s -X POST http://localhost:8000/v1/api-keys \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-Workspace-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"name":"n8n","scopes":["leads:read","leads:write","verify:run","exports:run","optout:write","webhooks:write"]}' | jq .
```

Save the `key` (shown only once). Example: `ef_xxxxxxxx.yyyyyyyy`.

---

## Lead Flow and How to Find the Contact

1. **Add lead:** `POST /v1/leads` (or bulk `POST /v1/leads/bulk`) with `first_name`, `last_name`, `domain`, `company`, etc. The lead is saved **without email** (`email_best` empty) until verified.

2. **Search/verify the contact (find the email):**
   - **By saved lead:** `POST /v1/leads/{lead_id}/verify` → queues a job that generates email candidates from lead's name + domain, picks the best one and updates the lead. Returns `job_id`. Check status with `GET /v1/jobs/{job_id}`; when complete the lead will have `email_best` and `verification_status`.
   - **Stateless (without saving):** `POST /v1/verify` with body `{ "first_name", "last_name", "domain" }` → returns immediately `candidates` and `best` (best email). Doesn't update any lead; useful for testing or integration flows where you don't want to persist.

3. **In the frontend:** In Dashboard → Leads there's a **Verify** button per row. Clicking it queues the job and the UI polls `GET /v1/jobs/{job_id}` until completion; then the list updates. **Important:** the job is executed by the **Celery worker**. If the worker isn't running, the job never executes and verification "does nothing". Check with `docker compose ps` that `mailprobe-worker-1` is **Up**.

---

## Postman Collection

In `postman/Mailprobe-API.postman_collection.json` there's a ready-to-import collection for Postman:

1. **Import:** Postman → Import → upload the JSON (or drag the file).
2. **Variables:** `base_url` = `http://localhost:8000`; after running **Login** it saves `access_token`; after **List workspaces** it saves `workspace_id`. For API Key: create a key and set it in `api_key`.
3. **Auth:** By default the collection uses Bearer (`access_token`). Requests requiring workspace in UI use header `X-Workspace-Id: {{workspace_id}}`. The "Auth with API Key" folder has examples using only `X-API-Key: {{api_key}}` (no workspace in header).

Includes: Health, Auth (register/login/refresh/me), Workspaces, Leads (create/bulk/list/get/verify), Verify stateless, Jobs, Opt-out, Exports, Webhooks, Usage, API Keys and API Key examples.

---

## cURL Examples for n8n

Base: `BASE=http://localhost:8000` and `KEY=ef_xxx.yyy` (your API key). No Bearer needed if using API key.

### 1) Create/update lead (upsert)

```bash
curl -s -X POST "$BASE/v1/leads" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: lead-1-john-smith" \
  -d '{
    "first_name": "John",
    "last_name": "Smith",
    "title": "Head of Sales",
    "company": "Example Inc",
    "domain": "example.com",
    "linkedin_url": "https://www.linkedin.com/in/john-smith-example/",
    "source": "linkedin_manual",
    "lawful_basis": "legitimate_interest",
    "purpose": "b2b_sales_outreach"
  }' | jq .
```

### 2) Bulk upsert leads (up to N)

```bash
curl -s -X POST "$BASE/v1/leads/bulk" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: bulk-import-001" \
  -d '{
    "leads": [
      {
        "first_name": "John",
        "last_name": "Smith",
        "company": "Example Inc",
        "domain": "example.com",
        "linkedin_url": "https://www.linkedin.com/in/john-smith-example/",
        "source": "csv_import"
      },
      {
        "first_name": "Jane",
        "last_name": "Doe",
        "company": "Example Inc",
        "domain": "example.com",
        "linkedin_url": "https://www.linkedin.com/in/jane-doe-example/",
        "source": "csv_import"
      }
    ]
  }' | jq .
```

### 3) Queue lead verification

```bash
# First get a lead_id (from list or creation)
curl -s -X POST "$BASE/v1/leads/1/verify" \
  -H "X-API-Key: $KEY" \
  -H "Idempotency-Key: verify-lead-1" | jq .
# Response: { "data": { "job_id": "uuid" } }
```

### 4) Stateless verification (name + domain → candidates + best)

```bash
curl -s -X POST "$BASE/v1/verify" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Smith",
    "domain": "example.com"
  }' | jq .
```

### 5) Job status

```bash
curl -s "$BASE/v1/jobs/<JOB_ID>" \
  -H "X-API-Key: $KEY" | jq .
```

### 6) Lead details

```bash
curl -s "$BASE/v1/leads/1" \
  -H "X-API-Key: $KEY" | jq .
```

### 7) List leads (pagination and filters)

```bash
curl -s "$BASE/v1/leads?page=1&page_size=20&verification_status=valid&domain=example.com" \
  -H "X-API-Key: $KEY" | jq .
```

### 8) Opt-out (unsubscribe)

```bash
# By email
curl -s -X POST "$BASE/v1/optout" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "reason": "user request"}' | jq .

# By lead_id
curl -s -X POST "$BASE/v1/optout" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1, "reason": "unsubscribe"}' | jq .
```

### 9) Export CSV (async)

```bash
curl -s -X POST "$BASE/v1/exports/csv" \
  -H "X-API-Key: $KEY" \
  -H "Idempotency-Key: export-001" | jq .
# Response: { "data": { "job_id": "uuid" } }
# Poll: GET /v1/jobs/<job_id> → result.csv contains CSV in base64 or text
```

### 10) Webhooks (register and test)

```bash
# Register webhook (events: lead.created, lead.updated, verification.completed, export.completed, optout.created)
curl -s -X POST "$BASE/v1/webhooks" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-n8n.com/webhook/mailprobe",
    "events": ["verification.completed", "export.completed"]
  }' | jq .

# Test
curl -s -X POST "$BASE/v1/webhooks/test" -H "X-API-Key: $KEY" | jq .
```

### 11) Usage (quota)

```bash
curl -s "$BASE/v1/usage" -H "X-API-Key: $KEY" | jq .
```

---

## API Response Format

- Success: `{ "data": ..., "error": null }`
- Error: `{ "data": null, "error": { "code": "...", "message": "...", "details": {} } }`
- Pagination: `data.items`, `data.page`, `data.page_size`, `data.total`
- Jobs: `data.job_id`, `data.status` (queued|running|succeeded|failed), `data.result`, `data.error`

---

## Example n8n Workflow (JSON)

Typical flow: receive webhook/Google Sheet → upsert lead → queue verification → wait for `verification.completed` webhook → if valid/risky, write to Sheets/CRM.

You can import an n8n workflow with:

1. **Webhook** or **Google Sheets** (trigger): new lead (first_name, last_name, company, domain, linkedin_url).
2. **HTTP Request** – POST `/v1/leads` with body from step 1, header `X-API-Key` and `Idempotency-Key` (e.g. `n8n-{{ $runId }}-{{ $item.id }}`).
3. **HTTP Request** – POST `/v1/leads/{{ $json.data.id }}/verify` (queue verification).
4. **Webhook** (wait): public n8n URL that receives `verification.completed` event; verify HMAC signature with webhook secret.
5. **IF** – `event === 'verification.completed'` and `data.verification_status` in ['valid','risky'].
6. **Google Sheets / CRM** – add row with lead + email_best + status.

Minimal example (save as `n8n_workflow_mailprobe.json` and import in n8n):

```json
{
  "name": "Mailprobe: Lead → Verify → Webhook → Sheets",
  "nodes": [
    {
      "id": "webhook_trigger",
      "name": "Webhook Lead",
      "type": "n8n-nodes-base.webhook",
      "position": [0, 0],
      "parameters": { "path": "incoming-lead", "httpMethod": "POST" }
    },
    {
      "id": "create_lead",
      "name": "Upsert Lead",
      "type": "n8n-nodes-base.httpRequest",
      "position": [220, 0],
      "parameters": {
        "method": "POST",
        "url": "=http://localhost:8000/v1/leads",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            { "name": "X-API-Key", "value": "={{ $env.MAILPROBE_API_KEY }}" },
            { "name": "Idempotency-Key", "value": "=n8n-{{ $runId }}-{{ $item.id }}" }
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            { "name": "first_name", "value": "={{ $json.body.first_name }}" },
            { "name": "last_name", "value": "={{ $json.body.last_name }}" },
            { "name": "company", "value": "={{ $json.body.company }}" },
            { "name": "domain", "value": "={{ $json.body.domain }}" },
            { "name": "linkedin_url", "value": "={{ $json.body.linkedin_url }}" },
            { "name": "source", "value": "n8n_webhook" }
          ]
        }
      }
    },
    {
      "id": "enqueue_verify",
      "name": "Queue Verification",
      "type": "n8n-nodes-base.httpRequest",
      "position": [440, 0],
      "parameters": {
        "method": "POST",
        "url": "=http://localhost:8000/v1/leads/{{ $json.data.id }}/verify",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            { "name": "X-API-Key", "value": "={{ $env.MAILPROBE_API_KEY }}" }
          ]
        }
      }
    }
  ],
  "connections": {
    "Webhook Lead": { "main": [[{ "node": "Upsert Lead", "type": "main", "index": 0 }]] },
    "Upsert Lead": { "main": [[{ "node": "Queue Verification", "type": "main", "index": 0 }]] }
  }
}
```

Configure in n8n the environment variable `MAILPROBE_API_KEY` with your API key.

---

## Repository Structure (monorepo)

```
mailprobe/
├── backend/           # FastAPI + Alembic + Celery
│   ├── app/
│   │   ├── api/v1/    # v1 routes
│   │   ├── core/      # config, db, security
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/  # verifier, email_patterns, usage_plan
│   │   └── tasks/     # Celery: verify, exports, webhooks, retention
│   ├── alembic/
│   ├── scripts/       # create_workspace
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/          # Next.js (TypeScript)
│   ├── src/app/
│   ├── package.json
│   └── Dockerfile
├── examples/
│   └── leads.csv      # sample_leads.csv
├── docker-compose.yml
└── README.md
```

## Migrations

```bash
cd backend
alembic -c alembic.ini upgrade head
alembic -c alembic.ini revision -m "desc"  # new revision
```

## Tests (backend)

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

## Development

### Branch Protection

The `main` branch is protected:
- **No direct commits allowed** (requires PR)
- **CI must pass** (`backend-tests`, `frontend-tests`) before merging
- **Applies to everyone**, including admins
- **Force push blocked**

GitHub Actions only runs on PRs (not on push to main).

### Git Hooks

The project includes git hooks that are automatically installed with `./validate.sh`:

| Hook | Source file | Validations |
|------|-------------|-------------|
| **pre-commit** | `scripts/pre-commit.sh` | Secrets, file size, ruff, eslint, TypeScript, pytest, test count |
| **pre-push** | `scripts/pre-push.sh` | Commit format (Conventional Commits) |

Manual installation:

```bash
cp scripts/pre-commit.sh .git/hooks/pre-commit
cp scripts/pre-push.sh .git/hooks/pre-push
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

### Test Rule

Each commit modifying Python code in `backend/app/` **must add at least 1 new test**. The pre-commit verifies this automatically.

For commits that don't require tests (typos, config, frontend-only):

```bash
# Skip only test count verification (other validations remain active)
SKIP_TEST_COUNT=1 git commit -m "fix: typo in message"
```

### Pull Requests

The project includes a PR template in `.github/PULL_REQUEST_TEMPLATE.md`. To validate before creating a PR:

```bash
./scripts/validate-pr.sh [base-branch]
```

The script verifies:
- Correct branch (not main)
- Commits follow Conventional Commits
- Tests pass
- Linting OK
- No secrets

### Full Validation

```bash
./validate.sh              # Validate everything (installs hooks if missing)
./validate.sh --fix        # Auto-fix linters
./validate.sh --skip-tests # Without tests (faster)
./validate.sh --backend    # Backend only
./validate.sh --frontend   # Frontend only
```

## Deploy (Render / Fly / DO)

- **Backend:** Web service (uvicorn). Variables: `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS` (include localhost:3001 and :3002 for prod and dev frontend).
- **Worker:** Background service (Celery worker).
- **Beat:** Cron service (Celery beat) optional for retention.
- **Frontend:** static/SSR with `NEXT_PUBLIC_API_URL` pointing to backend.
- **PostgreSQL** and **Redis** managed (Render, Upstash, etc.).

---

## Spain / GDPR Compliance (LOPDGDD)

- Required fields in leads: `source`, `lawful_basis` (default `legitimate_interest`), `purpose` (`b2b_sales_outreach`), `collected_at`.
- Opt-out: `POST /v1/optout`; blocks export and future verification for that email/domain/lead.
- Retention: scheduled job (Celery beat) anonymizes inactive leads > X months (configurable).
- Audit: `AuditLog` table for relevant actions.

## Notes

- No LinkedIn scraping; data comes via CSV, API or n8n.
- No emails sent; only find/verify and export.
- Idempotency: `Idempotency-Key` header in POST for leads, verify and exports.
- Webhooks: HMAC signature, retries with backoff, DLQ for failures.
