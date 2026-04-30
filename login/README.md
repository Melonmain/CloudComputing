# Login Service

Stand-alone FastAPI service for authentication. It stores users in a small SQLite database and returns JWTs for successful login or registration.

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

## Storage

By default the service uses `sqlite:///./data/login.db`.
