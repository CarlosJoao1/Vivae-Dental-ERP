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

## Deploy na Render

Este repositório inclui `render.yaml` com dois serviços:
- `vivae-backend` (web, Python): inicia via `gunicorn app:create_app()`
- `vivae-frontend` (static): build `npm ci && npm run build`, publica `dist/` e tem rewrite SPA

Variáveis obrigatórias (definir no dashboard da Render):
- `SECRET_KEY` (web)
- `JWT_SECRET_KEY` (web)
- `MONGO_URI` (web) – ex: string Atlas `mongodb+srv://.../vivae_dental_erp`

Variáveis ligadas automaticamente:
- `FRONTEND_ORIGINS` (web) vem da URL do serviço estático
- `VITE_API_BASE` (static) vem da URL do backend

Passos:
1. Criar Blueprint no Render apontando para este repo.
2. Confirmar que os dois serviços aparecem com nomes `vivae-backend` e `vivae-frontend`.
3. Definir `SECRET_KEY`, `JWT_SECRET_KEY`, `MONGO_URI` no serviço `vivae-backend`.
4. Deploy; o backend expõe `/api/health` e o frontend faz chamadas para `${VITE_API_BASE}/api`.

## Dev offline (sem Docker)

Backend:
1. Copie `backend/.env.example` para `backend/.env` e ajuste (SECRET_KEY/JWT_SECRET_KEY para dev, MONGO_URI local)
2. Crie e ative um venv e instale dependências:
	- Windows PowerShell
	  - python -m venv .venv
	  - .venv\\Scripts\\Activate.ps1
	  - pip install -r backend/requirements.txt
3. Inicie o backend:
	- python backend/app.py

Frontend:
1. Copie `frontend/.env.example` para `frontend/.env` e ajuste VITE_API_BASE
2. Instale e rode:
	- cd frontend
	- npm ci
	- npm run dev
