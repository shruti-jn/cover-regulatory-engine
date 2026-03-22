# Railway Deployment Topology

Cover deploys to Railway as a three-service topology:

- `api`: built from `docker/backend.Dockerfile`, serves the FastAPI application on port `8000`.
- `web`: built from `docker/frontend.Dockerfile`, serves the built React application via Nginx on port `80`.
- `Postgres`: managed Railway PostgreSQL with `postgis` and `pgvector` extensions enabled.

Operational notes:

- `api` reads `DATABASE_URL` and `DATABASE_PUBLIC_URL` from Railway-managed database service bindings.
- `web` is static and depends only on the built frontend bundle.
- No AWS-specific infrastructure is introduced; Railway remains the sole deployment target specified by the architecture.
