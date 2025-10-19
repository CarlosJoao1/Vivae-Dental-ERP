# 🔧 Troubleshooting: Cache do Browser

## Problema: "Form component coming soon" ainda aparece

Se você está a ver a mensagem **"Form component coming soon! API is ready at: /api/production/masterdata/items"** quando clica em **Edit** ou **Create**, isso significa que o browser está a usar uma versão antiga em cache.

## ✅ Solução: Limpar Cache do Browser

### Opção 1: Hard Refresh (Recomendado)
1. **Chrome/Edge/Brave**: 
   - Windows: `Ctrl + Shift + R` ou `Ctrl + F5`
   - Mac: `Cmd + Shift + R`

2. **Firefox**: 
   - Windows: `Ctrl + Shift + R` ou `Ctrl + F5`
   - Mac: `Cmd + Shift + R`

3. **Safari**: 
   - Mac: `Cmd + Option + R`

### Opção 2: Limpar Cache Manualmente
1. Abrir DevTools (F12)
2. **Chrome/Edge**: 
   - Right-click no botão Refresh (ao lado da URL)
   - Selecionar **"Empty Cache and Hard Reload"**

3. **Firefox**:
   - Settings → Privacy & Security → Cookies and Site Data → Clear Data
   - Marcar "Cached Web Content"
   - Click Clear

### Opção 3: Modo Incognito/Private
- Abrir uma janela privada/incognito
- Navegar para http://localhost:5173
- Fazer login novamente
- Testar os formulários

### Opção 4: Forçar Rebuild (Se nada funcionar)
```bash
# Parar containers
docker-compose down

# Remover volumes (cuidado: remove dados)
docker-compose down -v

# Rebuild e iniciar
docker-compose up --build -d

# Aguardar 30 segundos e testar
```

## 🔍 Verificar se os Formulários Estão Carregados

1. **Abrir DevTools** (F12)
2. Ir à tab **Network**
3. Filtrar por **JS** ou **tsx**
4. Fazer Hard Refresh (Ctrl+Shift+R)
5. Procurar por:
   - `ItemForm.tsx` ou `ItemForm.tsx.js`
   - `UOMForm.tsx` ou `UOMForm.tsx.js`
   - `LocationForm.tsx`
   - `SupplierForm.tsx`
   - `ProductionMasterData.tsx`

Se estes ficheiros aparecerem com **Status 200** (verde), significa que foram carregados corretamente.

## 🐛 Se ainda não funcionar

### Verificar Console do Browser
1. Abrir DevTools (F12)
2. Tab **Console**
3. Procurar por erros vermelhos
4. Se vir erros como:
   - `Module not found` → Problema de build
   - `Cannot read property` → Problema de dados
   - `401 Unauthorized` → Problema de autenticação

### Verificar Network Tab
1. DevTools → **Network**
2. Clicar em "Edit" ou "Create"
3. Ver se há pedidos falhados
4. Se vir **404** nos ficheiros tsx → Problema de build
5. Se vir **401** nos pedidos API → Token expirado

### Logs do Frontend
```bash
# Ver logs em tempo real
docker-compose logs -f frontend

# Procurar por erros
docker-compose logs frontend | grep -i error
```

## ✅ Como Saber se Funcionou

Quando clicar em **"➕ Create New"** ou **"✏️ Edit"**, deve ver:

### Para Items:
- Modal grande (max-w-2xl)
- Título: **"➕ Create Item"** ou **"✏️ Edit Item"**
- 8 campos: Item No., Description, Description 2, Item Type, Base UOM, Lead Time, Unit Cost, Status
- Botões: Cancel, Create/Update
- **NÃO deve ver**: "Form component coming soon"

### Para UOMs:
- Modal pequeno (max-w-md)
- Título: **"➕ Create UOM"** ou **"✏️ Edit UOM"**
- 3 campos: Code, Description, Decimals
- **NÃO deve ver**: "Form component coming soon"

### Para Locations:
- Modal médio (max-w-2xl)
- Título: **"➕ Create Location"** ou **"✏️ Edit Location"**
- Campos: Code, Name, Address, City, Postal Code, Country
- Checkboxes: Default, Blocked
- **NÃO deve ver**: "Form component coming soon"

### Para Suppliers:
- Modal grande (max-w-3xl)
- Título: **"➕ Create Supplier"** ou **"✏️ Edit Supplier"**
- 4 secções: Basic Info, Contact, Address, Business Terms
- **NÃO deve ver**: "Form component coming soon"

## 📝 Notas

- O código foi atualizado no commit `54a48b5`
- Todos os formulários foram implementados e testados
- Se ainda vir "Form component coming soon", é 100% cache do browser
- O Vite às vezes demora alguns segundos para recompilar após mudanças

## 🚀 Teste Rápido

Depois de limpar o cache:

1. Ir para: http://localhost:5173/production/masterdata
2. Click **"➕ Create New"** (tab Items)
3. **Deve ver**: Formulário completo com 8 campos
4. **NÃO deve ver**: "Form component coming soon"

Se ainda vir a mensagem antiga:
1. ❌ Fechar TODAS as tabs do localhost:5173
2. ❌ Fechar o browser completamente
3. ✅ Abrir browser novo
4. ✅ Navegar para http://localhost:5173
5. ✅ Fazer login
6. ✅ Testar novamente

---

**Última atualização**: October 20, 2025  
**Commit com formulários**: 54a48b5  
**Branch**: feature/production-navpp
