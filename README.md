# Mailprobe

Producto listo para producción: encontrar y verificar emails B2B, multi-tenant, integrado con **n8n** (webhooks, API estable, API Keys, idempotencia). Cumplimiento España/GDPR (LOPDGDD).

**Stack:** Backend Python + FastAPI, PostgreSQL, Celery + Redis, Frontend Next.js (TypeScript). Deploy: Docker Compose local; fácil en Render/Fly/DigitalOcean/Kubernetes.

---

## Requisitos

- Docker y Docker Compose
- (Opcional local) Python 3.12+, Node 20+

---

## Servicios externos y posibles costes

Este proyecto **no usa APIs de pago** para la lógica core (encontrar/verificar emails). Los únicos “servicios externos” son infraestructura y, opcionalmente, billing.

| Servicio | Uso | Coste |
|----------|-----|--------|
| **PostgreSQL** | Base de datos (leads, usuarios, jobs, etc.) | **Gestionado:** Render ~7 €/mes, Fly.io ~5 €/mes, Neon/Supabase free tier. **Self-hosted:** 0 € si ya tienes servidor. |
| **Redis** | Cola Celery (jobs, webhooks) | **Gestionado:** Upstash free tier (10k comandos/día), Redis Cloud free. **Self-hosted:** 0 €. |
| **DNS (MX lookup)** | Resolución MX para verificación | **Resolvedor del sistema** (lib `dnspython`). No usamos API de pago (Google DNS, etc.). **0 €**. |
| **SMTP (probe)** | Conexión a servidores MX de los dominios que verificas (Gmail, O365, etc.) | **No enviamos correo.** Solo hacemos RCPT TO a *sus* servidores. **0 €** (no hay SendGrid, SES, etc.). **Nota:** En muchos entornos (Docker, cloud) el **puerto 25** está bloqueado o limitado; la verificación SMTP puede fallar o tardar. Timeout configurable: `SMTP_TIMEOUT_SECONDS` (default 5). |
| **Búsqueda web (opcional)** | Comprobar si el email aparece en páginas públicas | **Opcional (configurable por workspace).** Si el MX no responde (firewall, Barracuda...) se busca si el email aparece en la web. Providers: **Serper.dev** (Google, 2500/mes gratis) o **Bing** (retirado agosto 2025). Se configura en **Dashboard → Configuración**. |
| **Webhooks outbound** | Llamadas HTTP a tus URLs (n8n, etc.) | **0 €** (solo tráfico saliente de tu servidor). |
| **Stripe** | Billing (planes de pago) | **Solo si lo integras.** Modelo preparado en BD (`stripe_customer_id`, etc.) pero no implementado. Stripe cobra ~1,5 % + 0,25 € por transacción. |

**Resumen:**  
- **Local / self-hosted:** coste 0 € en servicios externos (solo tu máquina/servidor).  
- **Deploy gestionado (Render/Fly/DO):** coste típico **~5–15 €/mes** (Postgres + Redis + 1–2 instancias).  
- **Sin coste por verificación:** no hay proveedor externo de “email verification API” (ZeroBounce, NeverBounce, etc.); la verificación es propia (MX + SMTP probe). Opcionalmente puedes añadir búsqueda web (Serper.dev o Bing) para marcar si el email aparece en fuentes públicas; cada workspace lo configura con su propia API key en **Dashboard → Configuración**.

---

## Verificación sin SMTP (entornos con puerto 25 bloqueado)

El puerto 25 (SMTP) está bloqueado en muchos entornos:
- **Docker Desktop (macOS/Windows):** El puerto 25 outbound está filtrado.
- **Cloud providers:** AWS, GCP, Azure bloquean o limitan el puerto 25 por defecto.
- **ISPs residenciales:** Muchos bloquean el puerto 25 para prevenir spam.

### Detección automática

El sistema detecta automáticamente cuando SMTP está bloqueado:
- Si hay timeouts a 3+ servidores MX distintos en 5 minutos, se activa el flag `smtp_blocked`.
- El flag se guarda en Redis con TTL de 15 minutos.
- Mientras está activo, las verificaciones **no intentan probes SMTP** (ahorra tiempo y recursos).

### Señales alternativas

Cuando SMTP no está disponible, el verificador usa señales alternativas:

| Señal | Descripción | Puntos |
|-------|-------------|--------|
| **MX** | Registros MX encontrados | +20 |
| **SPF** | Registro SPF configurado | +10 |
| **DMARC** | Política DMARC configurada | +10 |
| **Provider** | Proveedor conocido (Google, Microsoft, etc.) | +10 |
| **Web** | Email encontrado en fuentes públicas | +15 |

### Estados de verificación

| Estado | Significado |
|--------|-------------|
| `valid` | SMTP confirmó que el mailbox existe (solo si SMTP disponible) |
| `risky` | Señales positivas (MX, SPF, DMARC) pero sin confirmación SMTP |
| `unknown` | SMTP disponible pero respuesta inconclusa (greylist real) |
| `invalid` | Formato malo, dominio desechable, sin MX, o SMTP rechazó (550) |

### Campos de API

La respuesta de verificación incluye señales detalladas:

```json
{
  "best_result": {
    "email": "juan.garcia@empresa.com",
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

### Recomendación para producción

Para verificación SMTP completa, despliega el worker en un VPS con puerto 25 abierto (OVH, Hetzner, DigitalOcean en regiones que lo permiten). El backend/API puede seguir en cloud con puerto 25 bloqueado; solo el worker Celery necesita acceso.

---

## Setup local (Docker Compose)

```bash
# Clonar / entrar al repo
cd mailprobe

# Copiar env
cp backend/.env.example backend/.env
# Ajustar JWT_SECRET_KEY y demás si quieres

# Levantar servicios
docker compose up -d

# Migraciones
docker compose run --rm backend alembic -c alembic.ini upgrade head

# Crear workspace y usuario admin (sustituir email)
docker compose run --rm backend python -m scripts.create_workspace --email admin@example.com --password changeme --workspace-name "Mi Empresa" --workspace-slug default
```

- **Backend API:** http://localhost:8000  
- **Docs Swagger:** http://localhost:8000/docs  
- **Frontend:** http://localhost:3001  

### Ver cambios en el frontend sin reconstruir

Solo debe estar **uno** de los dos frontends activo. Con el compose de desarrollo, **backend, frontend, worker y beat** usan montaje de código y hot reload (no hace falta reconstruir).

| Puerto | Cuándo | Qué es |
|--------|--------|--------|
| **3001** | `docker compose up -d` (sin dev) | Frontend **producción**: build fijo, sin hot reload. |
| **3002** | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` | Frontend **desarrollo**: código montado, `npm run dev`, hot reload. Backend con `uvicorn --reload`. Worker y beat con `watchmedo` (reinicio al cambiar `.py`). |

Si tienes los dos levantados, para dejar solo el de desarrollo: `docker compose stop frontend` y luego `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d frontend`. Para volver a producción: para el dev y `docker compose up -d frontend`.

**Opción A — Todo en Docker con hot reload**

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

- **Backend:** monta `./backend` y ejecuta `uvicorn --reload`; los cambios en Python se recargan solos.
- **Worker y beat:** usan la misma imagen que backend (con `watchdog`), montan `./backend` y ejecutan `watchmedo auto-restart`; al cambiar cualquier `.py` se reinician. Solo hace falta construir una vez: `docker compose build backend`.
- **Frontend:** monta `./frontend`, ejecuta `npm run dev`; Next.js recarga al editar. Se expone en **http://localhost:3002**.

**Opción B — Frontend en local**

```bash
cd frontend
npm install
npm run dev
```

Backend, Postgres y Redis siguen en Docker; el frontend en http://localhost:3001 usa la API en http://localhost:8000.

---

## Crear API Key (para n8n)

1. Iniciar sesión en el frontend (o usar `POST /v1/auth/login`).
2. Con el token, crear API key (o usar endpoint si lo expones en UI):

```bash
# Login
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme"}' | jq .

# Crear API Key (usa el access_token y X-Workspace-Id del workspace que te devolvió create_workspace, ej. 1)
curl -s -X POST http://localhost:8000/v1/api-keys \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-Workspace-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"name":"n8n","scopes":["leads:read","leads:write","verify:run","exports:run","optout:write","webhooks:write"]}' | jq .
```

Guarda el `key` (solo se muestra una vez). Ejemplo: `ef_xxxxxxxx.yyyyyyyy`.

---

## Flujo de un lead y cómo buscar el contacto

1. **Añadir lead:** `POST /v1/leads` (o bulk `POST /v1/leads/bulk`) con `first_name`, `last_name`, `domain`, `company`, etc. El lead se guarda **sin email** (`email_best` vacío) hasta que se verifica.

2. **Buscar/verificar el contacto (encontrar el email):**
   - **Por lead guardado:** `POST /v1/leads/{lead_id}/verify` → encola un job que genera candidatos de email a partir del nombre + dominio del lead, elige el mejor y actualiza el lead. Devuelve `job_id`. Consulta el estado con `GET /v1/jobs/{job_id}`; al completar el lead tendrá `email_best` y `verification_status`.
   - **Stateless (sin guardar):** `POST /v1/verify` con body `{ "first_name", "last_name", "domain" }` → devuelve al momento `candidates` y `best` (mejor email). No actualiza ningún lead; útil para probar o integrar en un flujo donde no quieres persistir.

3. **En el frontend:** En Dashboard → Leads hay un botón **Verificar** por fila. Al pulsarlo se encola el job y la UI hace poll a `GET /v1/jobs/{job_id}` hasta que termine; entonces se actualiza la lista. **Importante:** el job lo ejecuta el **worker de Celery**. Si el worker no está en marcha, el job nunca se ejecuta y la verificación “no hace nada”. Comprueba con `docker compose ps` que `mailprobe-worker-1` esté **Up**.

---

## Colección Postman

En `postman/Mailprobe-API.postman_collection.json` hay una colección lista para importar en Postman:

1. **Importar:** Postman → Import → sube el JSON (o arrastra el archivo).
2. **Variables:** `base_url` = `http://localhost:8000`; tras ejecutar **Login** se guarda `access_token`; tras **List workspaces** se guarda `workspace_id`. Para API Key: crear una clave y ponerla en `api_key`.
3. **Auth:** Por defecto la colección usa Bearer (`access_token`). Las peticiones que requieren workspace en UI usan header `X-Workspace-Id: {{workspace_id}}`. La carpeta "Auth con API Key" tiene ejemplos usando solo `X-API-Key: {{api_key}}` (sin workspace en header).

Incluye: Health, Auth (register/login/refresh/me), Workspaces, Leads (create/bulk/list/get/verify), Verify stateless, Jobs, Opt-out, Exports, Webhooks, Usage, API Keys y ejemplos con API Key.

---

## Ejemplos cURL para n8n

Base: `BASE=http://localhost:8000` y `KEY=ef_xxx.yyy` (tu API key). No hace falta Bearer si usas API key.

### 1) Crear/actualizar lead (upsert)

```bash
curl -s -X POST "$BASE/v1/leads" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: lead-1-marta-garcia" \
  -d '{
    "first_name": "Marta",
    "last_name": "García",
    "title": "Head of Sales",
    "company": "Ejemplo SA",
    "domain": "example.com",
    "linkedin_url": "https://www.linkedin.com/in/marta-garcia-ejemplo/",
    "source": "linkedin_manual",
    "lawful_basis": "legitimate_interest",
    "purpose": "b2b_sales_outreach"
  }' | jq .
```

### 2) Bulk upsert leads (hasta N)

```bash
curl -s -X POST "$BASE/v1/leads/bulk" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: bulk-import-001" \
  -d '{
    "leads": [
      {
        "first_name": "Marta",
        "last_name": "García",
        "company": "Ejemplo SA",
        "domain": "example.com",
        "linkedin_url": "https://www.linkedin.com/in/marta-garcia-ejemplo/",
        "source": "csv_import"
      },
      {
        "first_name": "Juan",
        "last_name": "Pérez",
        "company": "Ejemplo SA",
        "domain": "example.com",
        "linkedin_url": "https://www.linkedin.com/in/juan-perez-ejemplo/",
        "source": "csv_import"
      }
    ]
  }' | jq .
```

### 3) Encolar verificación de un lead

```bash
# Primero obtén un lead_id (listado o creación)
curl -s -X POST "$BASE/v1/leads/1/verify" \
  -H "X-API-Key: $KEY" \
  -H "Idempotency-Key: verify-lead-1" | jq .
# Respuesta: { "data": { "job_id": "uuid" } }
```

### 4) Verificación “stateless” (nombre + dominio → candidatos + best)

```bash
curl -s -X POST "$BASE/v1/verify" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Marta",
    "last_name": "García",
    "domain": "example.com"
  }' | jq .
```

### 5) Estado de un job

```bash
curl -s "$BASE/v1/jobs/<JOB_ID>" \
  -H "X-API-Key: $KEY" | jq .
```

### 6) Detalle de un lead

```bash
curl -s "$BASE/v1/leads/1" \
  -H "X-API-Key: $KEY" | jq .
```

### 7) Listado de leads (paginación y filtros)

```bash
curl -s "$BASE/v1/leads?page=1&page_size=20&verification_status=valid&domain=example.com" \
  -H "X-API-Key: $KEY" | jq .
```

### 8) Opt-out (baja)

```bash
# Por email
curl -s -X POST "$BASE/v1/optout" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "reason": "solicitud usuario"}' | jq .

# Por lead_id
curl -s -X POST "$BASE/v1/optout" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1, "reason": "baja"}' | jq .
```

### 9) Export CSV (async)

```bash
curl -s -X POST "$BASE/v1/exports/csv" \
  -H "X-API-Key: $KEY" \
  -H "Idempotency-Key: export-001" | jq .
# Respuesta: { "data": { "job_id": "uuid" } }
# Poll: GET /v1/jobs/<job_id> → result.csv contiene el CSV en base64 o texto
```

### 10) Webhooks (registro y test)

```bash
# Registrar webhook (eventos: lead.created, lead.updated, verification.completed, export.completed, optout.created)
curl -s -X POST "$BASE/v1/webhooks" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://tu-n8n.com/webhook/mailprobe",
    "events": ["verification.completed", "export.completed"]
  }' | jq .

# Test
curl -s -X POST "$BASE/v1/webhooks/test" -H "X-API-Key: $KEY" | jq .
```

### 11) Uso (cuota)

```bash
curl -s "$BASE/v1/usage" -H "X-API-Key: $KEY" | jq .
```

---

## Formato de respuesta API

- Éxito: `{ "data": ..., "error": null }`
- Error: `{ "data": null, "error": { "code": "...", "message": "...", "details": {} } }`
- Paginación: `data.items`, `data.page`, `data.page_size`, `data.total`
- Jobs: `data.job_id`, `data.status` (queued|running|succeeded|failed), `data.result`, `data.error`

---

## Ejemplo workflow n8n (JSON)

Flujo típico: recibir webhook/Google Sheet → upsert lead → encolar verificación → esperar webhook `verification.completed` → si valid/risky, escribir en Sheets/CRM.

Puedes importar en n8n un workflow con:

1. **Webhook** o **Google Sheets** (trigger): nuevo lead (nombre, apellido, empresa, dominio, linkedin_url).
2. **HTTP Request** – POST `/v1/leads` con body del paso 1, header `X-API-Key` y `Idempotency-Key` (ej. `n8n-{{ $runId }}-{{ $item.id }}`).
3. **HTTP Request** – POST `/v1/leads/{{ $json.data.id }}/verify` (encolar verificación).
4. **Webhook** (esperar): URL pública de n8n que reciba evento `verification.completed`; verificar firma HMAC con el secret del webhook.
5. **IF** – `event === 'verification.completed'` y `data.verification_status` in ['valid','risky'].
6. **Google Sheets / CRM** – añadir fila con lead + email_best + status.

Ejemplo mínimo (guardar como `n8n_workflow_mailprobe.json` e importar en n8n):

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
      "name": "Encolar Verificación",
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
    "Upsert Lead": { "main": [[{ "node": "Encolar Verificación", "type": "main", "index": 0 }]] }
  }
}
```

Configura en n8n la variable de entorno `MAILPROBE_API_KEY` con tu API key.

---

## Estructura del repo (monorepo)

```
mailprobe/
├── backend/           # FastAPI + Alembic + Celery
│   ├── app/
│   │   ├── api/v1/    # Rutas v1
│   │   ├── core/      # config, db, security
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/  # verifier, email_patterns, usage_plan
│   │   └── tasks/    # Celery: verify, exports, webhooks, retention
│   ├── alembic/
│   ├── scripts/      # create_workspace
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

## Migraciones

```bash
cd backend
alembic -c alembic.ini upgrade head
alembic -c alembic.ini revision -m "desc"  # nueva revisión
```

## Tests (backend)

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

## Desarrollo

### Git Hooks

El proyecto incluye hooks de git que se instalan automáticamente con `./validate.sh`:

| Hook | Archivo fuente | Validaciones |
|------|----------------|--------------|
| **pre-commit** | `scripts/pre-commit.sh` | Secretos, tamaño archivos, ruff, eslint, TypeScript, pytest, conteo de tests |
| **pre-push** | `scripts/pre-push.sh` | Formato de commits (Conventional Commits), advertencia push a main |

Instalación manual:

```bash
cp scripts/pre-commit.sh .git/hooks/pre-commit
cp scripts/pre-push.sh .git/hooks/pre-push
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

### Regla de tests

Cada commit que modifique código Python en `backend/app/` **debe añadir al menos 1 test nuevo**. El pre-commit lo verifica automáticamente.

Para commits que no requieren tests (typos, config, frontend-only):

```bash
# Saltar solo la verificación de tests (el resto de validaciones sigue activo)
SKIP_TEST_COUNT=1 git commit -m "fix: typo en mensaje"
```

### Pull Requests

El proyecto incluye un template de PR en `.github/PULL_REQUEST_TEMPLATE.md`. Para validar antes de crear un PR:

```bash
./scripts/validate-pr.sh [base-branch]
```

El script verifica:
- Rama correcta (no main)
- Commits siguen Conventional Commits
- Tests pasan
- Linting OK
- Sin secretos

### Validación completa

```bash
./validate.sh              # Valida todo (instala hooks si faltan)
./validate.sh --fix        # Auto-fix linters
./validate.sh --skip-tests # Sin tests (más rápido)
./validate.sh --backend    # Solo backend
./validate.sh --frontend   # Solo frontend
```

## Despliegue (Render / Fly / DO)

- **Backend:** servicio Web (uvicorn). Variables: `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS` (incluye localhost:3001 y :3002 para front prod y dev).
- **Worker:** servicio Background (Celery worker).
- **Beat:** servicio Cron (Celery beat) opcional para retención.
- **Frontend:** estático/SSR con `NEXT_PUBLIC_API_URL` apuntando al backend.
- **PostgreSQL** y **Redis** gestionados (Render, Upstash, etc.).

---

## Compliance España / GDPR (LOPDGDD)

- Campos obligatorios en leads: `source`, `lawful_basis` (por defecto `legitimate_interest`), `purpose` (`b2b_sales_outreach`), `collected_at`.
- Opt-out: `POST /v1/optout`; bloquea export y verificación futura para ese email/dominio/lead.
- Retención: job programado (Celery beat) anonimiza leads inactivos > X meses (config).
- Auditoría: tabla `AuditLog` para acciones relevantes.

## Notas

- No se hace scraping de LinkedIn; los datos entran por CSV, API o n8n.
- No se envían emails; solo encontrar/verificar y exportar.
- Idempotencia: header `Idempotency-Key` en POST de leads, verify y exports.
- Webhooks: firma HMAC, reintentos con backoff, DLQ para fallos.
