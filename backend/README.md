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

| Variable | Standard | Beschreibung |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/appdb` | Datenbankverbindung |

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
