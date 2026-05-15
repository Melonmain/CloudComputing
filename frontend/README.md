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
```

## Build (Produktion)

```bash
npm run build
npm start
```

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
