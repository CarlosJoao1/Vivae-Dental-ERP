# Vivae Dental ERP – Backend (Flask + MongoDB)

## Stack
- Flask 3, Flask-JWT-Extended, Flask-CORS
- MongoDB 7 (MongoEngine)
- JWT + Refresh tokens + expiração segura
- Multi-tenant por laboratório (tenants)

## Requisitos
- Docker Desktop (Windows/Linux/macOS)
- Porta backend: **5000**
- MongoDB: **27017**
- Base de dados: **vivae_dental_erp**

## Como correr
```bash
docker compose up --build
# abre: http://localhost:5000/api  (health)
```

### Login (seed automático)
- Utilizador: `admin`
- Password: `admin123`
- Laboratório seed: `Vivae Dental Lab`

## Endpoints principais
- `GET /api` – info raiz
- `GET /api/health` – health check
- `POST /api/auth/login` – {username, password} → access_token, refresh_token
- `POST /api/auth/refresh` – com refresh token
- `GET /api/auth/me` – dados do utilizador
- `GET /api/tenants` – lista de laboratórios (para dropdown no frontend)
- `GET/POST/PUT /api/masterdata/laboratories` – CRUD básico

## Notas
- CORS está ativo para `http://localhost:5173`.
- Para produção, usa um WSGI (Gunicorn) e variáveis seguras para secrets.
