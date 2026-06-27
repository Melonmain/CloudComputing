# CloudComputing — Cloud ToDo List

A 3-tier ToDo web application deployed to an **OpenStack** private cloud. A single
Python script ([`cloud-init.py`](cloud-init.py)) provisions the whole stack — network,
subnet, router, security groups, instances and two **Octavia load balancers** — from a
completely empty project, and configures each instance via cloud-init user-data.

## Architecture

```
                         ┌─────────────────────────────────────────────┐
   browser ──HTTP:80──►  │ frontend-lb (floating IP)                    │
                         │   └─► frontend instance(s)  :80  (Next.js)   │
                         └──────────────┬──────────────────────────────┘
                                        │  NEXT_PUBLIC_API_URL / NEXT_PUBLIC_LOGIN_URL
                                        │  (baked in at build time)
              ┌─────────────────────────┼─────────────────────────┐
              ▼                         ▼                          │
   ┌────────────────────┐   ┌──────────────────────┐              │
   │ login-service :8001│   │ backend-lb (float IP)│              │
   │ (floating IP)      │   │  └─► backend :8000    │              │
   │  FastAPI / JWT     │   │      FastAPI REST API │              │
   └─────────┬──────────┘   └──────────┬───────────┘              │
             │ :5432                    │ :5432                    │
             ▼                          ▼                          │
   ┌────────────────────┐   ┌──────────────────────┐              │
   │ login-database     │   │ userdata-database     │   private network only
   │ Postgres (users)   │   │ Postgres (todos)      │   (10.0.0.0/24)
   └────────────────────┘   └──────────────────────┘
```

A drawn version lives in [documentation/layout.drawio.png](documentation/layout.drawio.png).

### Components (5 instances)

| Instance | Tier | Port | Public? | Purpose |
|---|---|---|---|---|
| `frontend` | Next.js UI | 80 | via `frontend-lb` | Serves the web app |
| `backend` | FastAPI REST API | 8000 | via `backend-lb` | ToDo CRUD, validates JWTs |
| `login-service` | FastAPI auth | 8001 | own floating IP | Register / login, issues JWTs |
| `login-database` | PostgreSQL | 5432 | private only | `users` table |
| `userdata-database` | PostgreSQL | 5432 | private only | `todos` table |

The `backend` and `frontend` tiers sit behind Octavia load balancers and are
**stateless** (shared DB, shared `JWT_SECRET_KEY`), so they scale horizontally — see
[Scaling](#scaling).

## Networking & load balancing

`cloud-init.py` creates everything itself (each step is idempotent, so re-runs are safe):

- **Network** `CloudComp22-net` + **subnet** `10.0.0.0/24` + a **router** to the shared
  external network `ext_net` (gives instances outbound internet for `git clone` and
  enables floating IPs).
- **Security groups**: `ssh` (22), `icmp`, `postgres` (5432), `login` (8001),
  `backend` (8000), `frontend` (80).
- **Octavia load balancers** (`backend-lb`, `frontend-lb`): each is built as
  LB → listener → pool (`ROUND_ROBIN`) → TCP health monitor → members, and gets a
  **floating IP** on its VIP as the public entry point.

## Deployment

### Prerequisites

- Python 3 with [`apache-libcloud`](https://libcloud.apache.org/) and
  [`openstacksdk`](https://docs.openstack.org/openstacksdk/) installed.
- `root-ca.crt` present in the repo root (used to verify the OpenStack endpoints).
- An SSH public key at `~/.ssh/cloudcomp.pub` (the matching private key
  `~/.ssh/cloudcomp` is what you use to SSH into the instances). Generate with:
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/cloudcomp -N ""
  ```
- OpenStack credentials / group number configured at the top of `cloud-init.py`.

### Run

```bash
python3 cloud-init.py
```

The script tears down any previous deployment (load balancers, instances, the managed
security groups), then rebuilds the full stack. On completion it prints the public URLs:

```
=== Deployment complete ===
Frontend:      http://<frontend-lb-ip>        (N instance(s) behind LB)
Backend:       http://<backend-lb-ip>:8000    (N instance(s) behind LB)
Login service: http://<login-service-ip>:8001
```

> **Note:** the script returns once the VMs are *booted*. Each VM then clones the repo
> and builds its service via cloud-init — in particular the frontend's `npm build` takes
> a few extra minutes before port 80 answers (its LB member shows `ERROR` → `ONLINE`).

Which branch the instances clone is controlled by the `cloud-init-*.sh` scripts
(`git clone --branch <branch>`).

### Scaling

Set the replica counts near the top of `cloud-init.py`:

```python
NUM_BACKEND_INSTANCES = 1
NUM_FRONTEND_INSTANCES = 1
```

Each extra replica is added as a load-balancer pool member automatically. The hard cap is
the project's instance quota (default **10**; the two databases + login are always
singletons), so keep `(NUM_BACKEND-1) + (NUM_FRONTEND-1) ≤ free slots`.

### Teardown

Re-running `cloud-init.py` already removes the previous load balancers, instances and
security groups before redeploying. The network / subnet / router are left in place and
reused.

## Local development

Each service can run on its own — see the per-service READMEs:

- [backend/README.md](backend/README.md) — FastAPI REST API (port 8000)
- [frontend/README.md](frontend/README.md) — Next.js UI (port 3000 dev / 80 prod)
- [login/README.md](login/README.md) — FastAPI auth service (port 8001)

A [docker-compose.yml](docker-compose.yml) is also provided for running the stack locally.

## Data model

Both databases use database `appdb`, user `postgres` / `postgres`, port `5432`. The
`cloud-init-database.sh` script creates the tables (`CREATE TABLE IF NOT EXISTS`):

**`login-database` → `users`**
```sql
users (
    id            UUID PRIMARY KEY,
    username      TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**`userdata-database` → `todos`**
```sql
todos (
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL,
    title       TEXT NOT NULL,
    description TEXT,
    completed   BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Service interfaces

- **Login service** — `POST /auth/register`, `POST /auth/login` → JWT (cookie);
  `POST /auth/logout`; `GET /health`.
- **Backend** — `GET/POST /todos/`, `PUT/DELETE /todos/{id}` (JWT-protected);
  also mirrors `/auth/*`.

## Repository layout

```
.
├── cloud-init.py              # Orchestrator: provisions OpenStack + deploys everything
├── cloud-init-database.sh     # User-data: PostgreSQL + schema (login / userdata)
├── cloud-init-login.sh        # User-data: login service
├── cloud-init-backend.sh      # User-data: backend API
├── cloud-init-frontend.sh     # User-data: frontend
├── backend/                   # FastAPI REST API
├── frontend/                  # Next.js app
├── login/                     # FastAPI auth service
├── docker-compose.yml         # Local multi-service run
├── documentation/             # Architecture diagram
└── root-ca.crt                # CA cert for the OpenStack endpoints
```
