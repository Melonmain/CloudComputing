# CloudComputing: ToDo List
- Database (saves ToDos + users; postgres)
- Frontend (displays data from backend)
- Backend (executes database query; RestApi) ((scalable))
- Login Server (userId + paswordHash; returns jwt)

## Schnittstellen:
### Datenbank 1
Database query (login: postgres)
users (
    id UUID PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

### Datenbank 2
todos (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
);

### Backend
login(username, password) -> jwt-Token (cookie)
register(username, password)
getData(jwt-Token) -> json

### Login Server
login(username, password) -> jwt-Token (cookie)
register(username, password) -> jwt-Token