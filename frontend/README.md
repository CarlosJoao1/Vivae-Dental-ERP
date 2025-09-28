# Vivae Dental ERP – Frontend (React + TypeScript + Tailwind + Vite)

## Requisitos
- Node 18+ / 20+
- Backend Flask em `http://localhost:5000/api`

## Instalação
```bash
npm install
copy .env.example .env   # Windows PowerShell: Copy-Item .env.example .env
npm run dev
```

App: http://localhost:5173

### Config .env
```
VITE_API_URL=http://localhost:5000/api
```

## Funcionalidades
- Login com JWT + Refresh (tokens guardados em localStorage)
- Multi-tenant: seleção de laboratório no login (ou dropdown no topo)
- i18n: PT (default), EN, ES, FR, CN
- Layout: Sidebar fixa + Topbar (Theme toggle light/dark)
- Dashboard com **cards interativos** (lista vertical)
- Rotas protegidas via `<PrivateRoute>`

## Ligar ao backend
- Endpoint de login esperado: `POST /api/auth/login` -> `{ access_token, refresh_token, tenant_id?, user }`
- Refresh token: `POST /api/auth/refresh` -> `{ access_token }`
- Perfil: `GET /api/auth/me` -> `{ user }`
- Lista de tenants (opcional): `GET /api/tenants` -> `{ tenants: [{id, name}] }`
Se não existir `/api/tenants`, é usado um tenant mock `default`.
