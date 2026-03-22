# Local Development

This setup is for the product repo only:

- repo: `/Users/shruti/Software/cover-regulatory-engine`
- branch: `main`

It does not require deploying or running the Software Factory worktrees.

## 1. Prepare the environment

Use Python 3.11 or newer and Node 20 or newer.

```bash
cd /Users/shruti/Software/cover-regulatory-engine
cp .env.example .env
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

If you want live Google geocoding locally, add your API key to `.env`:

```bash
GOOGLE_MAPS_API_KEY=your-key-here
```

## 2. Start the local database

This project needs PostgreSQL with both `postgis` and `pgvector`.
The packaged local container binds to `localhost:5433` to avoid colliding with an existing local Postgres on `5432`.

```bash
cd /Users/shruti/Software/cover-regulatory-engine
docker compose -f compose.local.yaml up -d db
```

## 3. Run migrations

```bash
cd /Users/shruti/Software/cover-regulatory-engine
source .venv/bin/activate
alembic upgrade head
```

## 4. Seed a local admin user

Admin endpoints currently use a local placeholder auth model:

- send `Authorization: Bearer <admin-email>`
- the email must exist in the `users` table with role `ADMIN`

Seed one with:

```bash
cd /Users/shruti/Software/cover-regulatory-engine
source .venv/bin/activate
python scripts/seed_local_admin.py you@example.com
```

## 5. Run the backend

```bash
cd /Users/shruti/Software/cover-regulatory-engine
source .venv/bin/activate
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Useful checks:

- API root: `http://127.0.0.1:8000/`
- health: `http://127.0.0.1:8000/health`
- OpenAPI: `http://127.0.0.1:8000/docs`

## 6. Run the frontend

In another terminal:

```bash
cd /Users/shruti/Software/cover-regulatory-engine/frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

- app: `http://127.0.0.1:5173`

## 7. Stop services

```bash
cd /Users/shruti/Software/cover-regulatory-engine
docker compose -f compose.local.yaml down
```

To remove the local database volume too:

```bash
docker compose -f compose.local.yaml down -v
```
