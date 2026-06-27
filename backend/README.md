# Backend

FastAPI REST API mit PostgreSQL-Anbindung.

## Stack

- FastAPI 0.115
- SQLAlchemy 2.0 (sync)
- PostgreSQL 16 (psycopg2)
- pydantic-settings (Konfiguration via `.env`)

## Lokaler Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

## Konfiguration

Konfiguration via Umgebungsvariablen (oder `.env`). Im Cloud-Deployment werden diese
von [`cloud-init.py`](../cloud-init.py) automatisch gesetzt.

| Variable | Standard | Beschreibung |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/appdb` | Verbindung zur `userdata-database` (Tabelle `todos`) |
| `JWT_SECRET_KEY` | `CHANGE_ME_IN_PRODUCTION` | Secret zum Validieren der JWTs (muss mit dem Login-Service übereinstimmen) |
| `JWT_ALGORITHM` | `HS256` | Signaturalgorithmus der JWTs |
| `CORS_ORIGINS` | `http://localhost:3000` | Erlaubte Origins (kommagetrennt); im Deployment die Frontend-Floating-IP |

## Deployment

Im Cloud-Deployment läuft der Backend als `systemd`-Service auf Port 8000 hinter dem
Octavia-Load-Balancer `backend-lb`. Da der Service zustandslos ist (gemeinsame DB,
gemeinsames `JWT_SECRET_KEY`), kann er über `NUM_BACKEND_INSTANCES` horizontal skaliert
werden. Siehe [Haupt-README](../README.md).

## Endpunkte

| Methode | Pfad | Beschreibung |
|---|---|---|
| GET | `/todos/` | Alle Todos abrufen |
| POST | `/todos/` | Todo erstellen |
| PUT | `/todos/{id}` | Todo aktualisieren |
| DELETE | `/todos/{id}` | Todo löschen |
| POST | `/auth/login` | Anmelden |
| POST | `/auth/register` | Registrieren |
| POST | `/auth/logout` | Abmelden |

## Projektstruktur

```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   └── todo.py
│   ├── routers/
│   │   ├── todos.py
│   │   └── auth.py
│   └── services/
│       └── todo_service.py
└── requirements.txt
```
