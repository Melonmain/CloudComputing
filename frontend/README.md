# Frontend

Next.js 16 App für die Cloud Todo Applikation.

## Stack

- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS v4
- shadcn/ui

## Lokaler Start

```bash
npm install
npm run dev
```

App läuft auf http://localhost:3000

## Konfiguration

`.env.local` im `frontend/`-Verzeichnis anlegen:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_LOGIN_URL=http://localhost:8001
```

| Variable | Beschreibung |
|---|---|
| `NEXT_PUBLIC_API_URL` | Basis-URL des Backends (im Deployment der `backend-lb`) |
| `NEXT_PUBLIC_LOGIN_URL` | Basis-URL des Login-Service |

> **Wichtig:** `NEXT_PUBLIC_*`-Variablen werden zur **Build-Zeit** in das Bundle
> eingebacken. Im Cloud-Deployment setzt [`cloud-init.py`](../cloud-init.py) sie vor dem
> `npm build` auf die jeweiligen Floating-IPs.

## Build (Produktion)

```bash
npm run build
npm start
```

## Deployment

Im Cloud-Deployment wird das Frontend per cloud-init gebaut und als `systemd`-Service auf
Port 80 hinter dem Octavia-Load-Balancer `frontend-lb` betrieben. Siehe
[Haupt-README](../README.md).

## Projektstruktur

```
frontend/
├── app/
│   ├── dashboard/
│   ├── login/
│   ├── register/
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── layout/
│   ├── todos/
│   └── ui/
└── lib/
    ├── api.ts
    ├── auth.tsx
    └── theme.tsx
```
