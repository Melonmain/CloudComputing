# Login Service

Stand-alone FastAPI service for authentication. It stores users in a PostgreSQL database (the `users` table) and returns JWTs for successful login or registration.

## Run locally

```bash
cd login
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

API base: `http://localhost:8001`

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create a user and return a JWT |
| POST | `/auth/login` | Authenticate a user and return a JWT |
| POST | `/auth/logout` | Clear the auth cookie |
| GET | `/health` | Service health check |

## Configuration

Configured via environment variables (or `.env`). In the cloud deployment these are set
automatically by [`cloud-init.py`](../cloud-init.py).

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/appdb` | Connection to the `login-database` (table `users`) |
| `JWT_SECRET_KEY` | `CHANGE_ME_IN_LOGIN_SERVICE` | Secret used to sign JWTs (must match the backend) |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed origins (comma-separated); the frontend floating IP in the deployment |

## Deployment

In the cloud deployment the login service runs as a `systemd` service on port 8001 with
its own floating IP (it is not load-balanced). It shares `JWT_SECRET_KEY` with the
backend so tokens it issues are accepted there. See the [main README](../README.md).
