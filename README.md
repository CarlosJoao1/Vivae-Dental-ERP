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

	## Versionamento e Health Info

	- Endpoint: `GET /api/health/info` retorna `{ ok, version, branch, commit, build_time }`.
	- Versão por padrão é calculada como `v[AnoSemana].01` (ISO YearWeek), ex.: `v202542.01`.
	- Para fixar manualmente a versão no deploy, defina `APP_VERSION` no ambiente (Render ou `.env`).
	- O frontend exibe a versão no Topbar (lado esquerdo), obtendo-a do endpoint acima.

### SPA (React) – F5 em páginas internas dá Not Found em produção

Se ao fazer refresh em URLs como `/masterdata` no domínio de produção do frontend aparece “Not Found”, verifique:

- Serviço estático (Render): adicione uma regra de rewrite SPA para enviar qualquer caminho para `index.html`.
	- Em `render.yaml` já existe:
		- routes:
			- type: rewrite
				source: /*
				destination: /index.html
	- Se criou o serviço manualmente, configure esta regra no dashboard do Static Site.
- Use sempre o domínio do frontend (Static Site) para navegar. Se usar o domínio do backend e der refresh, o backend tenta redirecionar 404 não-API para o frontend preservando o path. Para isso, a env `FRONTEND_ORIGINS` do backend deve conter a URL do frontend (o `render.yaml` liga automaticamente).
- Testes rápidos:
	- Aceda a `https://<frontend>/qualquer/coisa` → deve carregar a app (index.html) e o router trata o caminho.
	- Aceda a `https://<backend>/masterdata` → deve redirecionar para o domínio do frontend mantendo `/masterdata` se `FRONTEND_ORIGINS` estiver definido.
