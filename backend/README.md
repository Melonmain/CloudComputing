# Todo API — FastAPI Backend

Cloud-native Todo REST API. Läuft im Mock-Modus (kein Datenbank-Zugriff nötig).

## Schnellstart

```bash
cd backend

# Virtuelle Umgebung erstellen und aktivieren
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Server starten
uvicorn app.main:app --reload
```

API läuft auf → http://localhost:8000  
Swagger UI →    http://localhost:8000/docs  
ReDoc →         http://localhost:8000/redoc

---

## Endpunkte

| Methode | Pfad                  | Beschreibung              |
|---------|-----------------------|---------------------------|
| GET     | /health               | Health-Check              |
| GET     | /todos/               | Alle Todos abrufen        |
| POST    | /todos/               | Neues Todo erstellen      |
| PUT     | /todos/{todo_id}      | Todo aktualisieren        |
| DELETE  | /todos/{todo_id}      | Todo löschen              |
| POST    | /auth/login           | Mock-Login (setzt Cookie) |
| POST    | /auth/register        | Mock-Registrierung        |
| POST    | /auth/logout          | Cookie löschen            |

---

## Projektstruktur

```
backend/
├── app/
│   ├── main.py              # FastAPI App-Instanz, CORS, Router-Registrierung
│   ├── core/
│   │   └── config.py        # Settings via pydantic-settings (.env)
│   ├── models/
│   │   └── todo.py          # Pydantic-Modelle: Todo, TodoCreate, TodoUpdate
│   ├── routers/
│   │   ├── todos.py         # CRUD-Endpunkte
│   │   └── auth.py          # Mock-Auth-Endpunkte
│   └── services/
│       └── todo_service.py  # Business-Logic (in-memory, austauschbar)
├── requirements.txt
└── README.md
```

---

## PostgreSQL anbinden (spätere Migration)

1. `requirements.txt`: Kommentar bei `asyncpg`, `sqlalchemy[asyncio]`, `alembic` entfernen.
2. `app/core/config.py`: `database_url` befüllen.
3. `app/models/todo.py`: SQLAlchemy-Modell `TodoModel` aus dem Kommentar aktivieren.
4. `app/services/todo_service.py`: In-Memory-Store durch async DB-Session ersetzen.
5. Alembic-Migrationen erstellen: `alembic init alembic && alembic revision --autogenerate`.

## Login-Server anbinden

- `app/routers/auth.py`: `TODO`-Kommentar ersetzen — HTTP-Call an externen Login-Server.
- JWT aus Response auslesen und als Cookie weiterreichen.
- `app/core/config.py`: `jwt_secret_key` aus Umgebungsvariable laden.
- Middleware hinzufügen, die JWT aus Cookie validiert und `user_id` in Request-State speichert.
