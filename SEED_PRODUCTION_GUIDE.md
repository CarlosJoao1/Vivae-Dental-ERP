# 🚀 Guia para Seed de Dados em Produção (Render)

## 🔐 AVISO DE SEGURANÇA

**NUNCA compartilhe ou commite credenciais reais!**

- ❌ Não inclua URIs reais do MongoDB em commits
- ❌ Não compartilhe senhas ou tokens de acesso
- ✅ Use variáveis de ambiente para credenciais
- ✅ Mantenha `.env` no `.gitignore`
- ✅ Use placeholders genéricos em documentação (ex: `<USERNAME>:<PASSWORD>`)

## ⚠️ IMPORTANTE - Leia Antes de Executar

Este processo irá criar dados de exemplo no seu ambiente de **PRODUÇÃO** no Render. Certifique-se de que:

1. ✅ Tem backup da base de dados de produção
2. ✅ Confirmou que deseja adicionar dados de exemplo
3. ✅ Tem as credenciais de acesso ao MongoDB de produção
4. ✅ Sabe o Laboratory ID correto para usar

## 📋 Pré-requisitos

### 1. Obter MongoDB URI de Produção

No painel do Render (https://dashboard.render.com):
1. Acesse seu serviço `vivae-backend`
2. Vá para **Environment**
3. Copie o valor de `MONGO_URI`

Exemplo (formato genérico):
```
mongodb+srv://<USERNAME>:<PASSWORD>@<CLUSTER>.mongodb.net/<DATABASE>?retryWrites=true&w=majority
```

⚠️ **IMPORTANTE**: Nunca compartilhe sua URI real com credenciais!

### 2. Obter Laboratory ID

Você precisa do ID do laboratório onde os dados serão criados. Pode obter de duas formas:

**Opção A: Via API**
```bash
# Obter token JWT
curl -X POST https://vivae-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"seu@email.com","password":"suasenha"}'

# Listar laboratórios
curl -X GET https://vivae-backend.onrender.com/api/tenants/laboratories \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Opção B: Via MongoDB Compass**
```javascript
// Conectar ao MongoDB com a URI de produção
// Executar query na collection 'laboratory':
db.laboratory.find({}, {_id: 1, name: 1})
```

## 🔧 Configuração Local

### 1. Configurar Variáveis de Ambiente

**Windows (PowerShell):**
```powershell
# Definir MongoDB URI de produção (substitua com sua URI real do Render)
$env:MONGO_URI_PRODUCTION = "mongodb+srv://<YOUR_USER>:<YOUR_PASSWORD>@<YOUR_CLUSTER>.mongodb.net/<YOUR_DB>"

# Definir Laboratory ID (opcional - será solicitado se não definido)
$env:PRODUCTION_LAB_ID = "<YOUR_LAB_ID>"
```

**Linux/Mac (Bash):**
```bash
# Definir MongoDB URI de produção (substitua com sua URI real do Render)
export MONGO_URI_PRODUCTION="mongodb+srv://<YOUR_USER>:<YOUR_PASSWORD>@<YOUR_CLUSTER>.mongodb.net/<YOUR_DB>"

# Definir Laboratory ID (opcional)
export PRODUCTION_LAB_ID="<YOUR_LAB_ID>"
```

### 2. Instalar Dependências (se necessário)

```bash
cd backend
pip install -r requirements.txt
```

## 🌱 Executar Seed em Produção

### Método 1: Com Variáveis de Ambiente Configuradas

```bash
cd backend/scripts
python seed_production_remote.py
```

### Método 2: Inline (uma linha)

**Windows PowerShell:**
```powershell
$env:MONGO_URI_PRODUCTION="<YOUR_MONGODB_URI>"; `
$env:PRODUCTION_LAB_ID="<YOUR_LAB_ID>"; `
python backend/scripts/seed_production_remote.py
```

**Linux/Mac:**
```bash
MONGO_URI_PRODUCTION="<YOUR_MONGODB_URI>" \
PRODUCTION_LAB_ID="<YOUR_LAB_ID>" \
python backend/scripts/seed_production_remote.py
```

## 📝 Processo de Confirmação

O script irá:

1. **Mostrar aviso de produção**
   - Solicitar confirmação explícita
   - Você deve digitar `YES I UNDERSTAND`

2. **Verificar dados existentes**
   - Mostrar quantos Items, Work Centers, BOMs já existem
   - Solicitar confirmação se dados existirem

3. **Criar dados de exemplo**
   - 3 UOMs (PCS, KG, M)
   - 2 Locations (MAIN, PROD)
   - 1 Supplier
   - 3 Items (1 Finished Good, 2 Raw Materials)
   - 2 Work Centers (MACHINING, ASSEMBLY)
   - 1 Machine Center (CNC-001)
   - 1 BOM certificado
   - 1 Routing certificado
   - 1 Production Order

## 🎯 Dados Criados

### Items
- **FG-DEMO-001**: Demo Finished Good (Produto Final)
- **RM-DEMO-001**: Demo Raw Material 1 (Matéria-Prima)
- **RM-DEMO-002**: Demo Raw Material 2 (Matéria-Prima)

### Work Centers
- **MACHINING**: Departamento de Maquinação (480 min/dia, 85% eficiência)
- **ASSEMBLY**: Departamento de Montagem (480 min/dia, 90% eficiência)

### Machine Centers
- **CNC-001**: Máquina CNC (420 min/dia, 80% eficiência)

### BOM (Bill of Materials)
- Item: FG-DEMO-001
- Versão: V1
- Status: Certified
- Componentes:
  - RM-DEMO-001: 2.0 KG (5% scrap)
  - RM-DEMO-002: 1.5 M (3% scrap)

### Routing
- Item: FG-DEMO-001
- Versão: V1
- Status: Certified
- Operações:
  1. CNC Machining (MACHINING, CNC-001): 30 min setup, 15 min run
  2. Assembly (ASSEMBLY): 15 min setup, 10 min run

### Production Order
- Número: PO-DEMO-001
- Status: Planned
- Quantidade: 10 PCS
- Due Date: +7 dias

## ✅ Verificação Pós-Seed

Após executar o seed com sucesso:

1. **Acesse o app de produção**: https://vivae-frontend.onrender.com
2. **Faça login** com suas credenciais
3. **Navegue para**: Production → Planning
4. **Verifique**:
   - Production Order PO-DEMO-001 aparece na lista
   - Status: Planned
   - Pode clicar para ver detalhes
5. **Teste workflows**:
   - Release order (Planned → Released)
   - Finish order (Released → Finished)

## 🔍 Troubleshooting

### Erro: "MONGO_URI_PRODUCTION environment variable not set"
**Solução**: Defina a variável de ambiente antes de executar o script

### Erro: "Connection failed"
**Soluções**:
- Verifique se a URI está correta
- Confirme que tem acesso à rede (VPN se necessário)
- Verifique se o IP está na whitelist do MongoDB Atlas

### Erro: "Laboratory ID is required"
**Solução**: Forneça o Laboratory ID via variável de ambiente ou quando solicitado

### Aviso: "Data already exists"
**Significa**: Já existem dados de produção para este laboratório
**Opção**: Pode continuar (criará dados adicionais) ou cancelar

## 🗑️ Limpeza de Dados (se necessário)

Se precisar remover os dados de exemplo depois:

```python
# Conectar ao MongoDB de produção via MongoDB Compass ou shell
# Executar queries para deletar os dados demo:

db.item.deleteMany({ item_no: /^(FG|RM)-DEMO-/ })
db.work_center.deleteMany({ code: /^(MACHINING|ASSEMBLY|CNC-)/ })
db.bom.deleteMany({ item_no: "FG-DEMO-001" })
db.routing.deleteMany({ item_no: "FG-DEMO-001" })
db.production_order.deleteMany({ order_no: /^PO-DEMO-/ })
db.uom.deleteMany({ code: { $in: ["PCS", "KG", "M"] } })
db.location.deleteMany({ code: { $in: ["MAIN", "PROD"] } })
db.supplier.deleteMany({ code: "SUP-001" })
```

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs do script para mensagens de erro detalhadas
2. Confirme todas as variáveis de ambiente estão corretas
3. Verifique conectividade com MongoDB Atlas
4. Consulte TECHNICAL_SPEC.md para detalhes dos modelos

## ⚡ Exemplo de Execução Completa

```powershell
# 1. Definir variáveis (substitua com seus valores reais)
$env:MONGO_URI_PRODUCTION = "mongodb+srv://<USER>:<PASS>@<CLUSTER>.mongodb.net/<DB>"
$env:PRODUCTION_LAB_ID = "<YOUR_LABORATORY_ID>"

# 2. Executar seed
cd c:\Python\scripts\Pessoal\dental_lab_erp_starter\Vivae-Dental-ERP\backend\scripts
python seed_production_remote.py

# 3. Output esperado:
# 🌱 VIVAE ERP - Production Data Seed (Remote)
# ============================================================
# 🏥 Target Laboratory: <YOUR_LABORATORY_ID>
# 🔗 MongoDB URI: mongodb+srv://<USER>:<PASS>@...
# 
# ⚠️  WARNING: PRODUCTION SEED OPERATION
# ============================================================
# [... confirmação ...]
# Type 'YES I UNDERSTAND' to proceed: YES I UNDERSTAND
# 
# 🔌 Connecting to production database...
# ✅ Connected successfully
# 
# 📊 Existing data in laboratory:
#   - Items: 0
#   - Work Centers: 0
#   - BOMs: 0
# 
# 🚀 Starting seed operation...
# [... processo de criação ...]
# 
# ============================================================
# ✅ SEED COMPLETED SUCCESSFULLY!
# ============================================================
```

---

**Nota**: Este script foi criado especificamente para ambiente de **produção**. Use com cuidado e sempre com backup!
