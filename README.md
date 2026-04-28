# Cloud Todo

Cloud-native To-Do-Applikation im Rahmen des Cloud Computing Praktikums.

## Architektur

| Komponente | Technologie | Port |
|---|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS | 3000 |
| Backend | FastAPI, SQLAlchemy, PostgreSQL | 8000 |
| Datenbank | PostgreSQL 16 | 5432 |
| Infrastruktur | OpenStack / Apache Libcloud | — |

## Lokale Entwicklung

**Voraussetzungen:** Docker Desktop

```bash
docker-compose up --build
```

Startet Datenbank, Backend und Frontend in der richtigen Reihenfolge.

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

## Deployment (OpenStack)

```bash
pip install apache-libcloud
python cloud-init.py
```

Das Skript erstellt VMs für Datenbank, Backend und Frontend, verteilt die IP-Adressen automatisch und startet alle Dienste per systemd.

## Projektstruktur

```
.
├── backend/          # FastAPI REST API
├── frontend/         # Next.js App
├── cloud-init.py     # OpenStack Provisioning
├── cloud-init-backend.sh
├── cloud-init-frontend.sh
└── docker-compose.yml
```
