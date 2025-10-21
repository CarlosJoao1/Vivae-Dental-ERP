#!/bin/bash
# VIVAE ERP - Seed Production Data to Render
# Script Bash simplificado para Linux/Mac

echo -e "\n\033[1;36m🌱 VIVAE ERP - Production Data Seed Helper\033[0m"
echo "============================================================"

# 1. Verificar se está no diretório correto
if [ ! -f "backend/scripts/seed_production_remote.py" ]; then
    echo -e "\n\033[1;31m❌ Error: Must run from project root directory\033[0m"
    echo -e "\033[1;33mCurrent: $(pwd)\033[0m"
    echo -e "\033[1;33mExpected: .../Vivae-Dental-ERP/\033[0m"
    exit 1
fi

# 2. Solicitar MongoDB URI
echo -e "\n\033[1;32m📝 Step 1: MongoDB Production URI\033[0m"
echo "Get this from Render Dashboard → vivae-backend → Environment → MONGO_URI"
read -p "Enter MONGO_URI_PRODUCTION: " mongo_uri

if [ -z "$mongo_uri" ]; then
    echo -e "\033[1;31m❌ MongoDB URI is required\033[0m"
    exit 1
fi

# 3. Solicitar Laboratory ID
echo -e "\n\033[1;32m📝 Step 2: Laboratory ID\033[0m"
echo "Get this from your database or via API"
echo "Leave blank if you want to be prompted during seed"
read -p "Enter PRODUCTION_LAB_ID (optional): " lab_id

# 4. Confirmar dados
echo -e "\n\033[1;33m📋 Configuration:\033[0m"
echo "  MongoDB URI: ${mongo_uri:0:50}..."
if [ -n "$lab_id" ]; then
    echo "  Laboratory ID: $lab_id"
else
    echo "  Laboratory ID: Will be prompted during seed"
fi

# 5. Confirmar execução
echo -e "\n\033[1;31m⚠️  WARNING: This will seed data to PRODUCTION!\033[0m"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "\n\033[1;33m❌ Operation cancelled\033[0m"
    exit 0
fi

# 6. Configurar variáveis de ambiente
export MONGO_URI_PRODUCTION="$mongo_uri"
if [ -n "$lab_id" ]; then
    export PRODUCTION_LAB_ID="$lab_id"
fi

# 7. Verificar se Python está disponível
echo -e "\n\033[1;36m🔍 Checking Python...\033[0m"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "\033[1;32m✅ Python found: $(python3 --version)\033[0m"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo -e "\033[1;32m✅ Python found: $(python --version)\033[0m"
else
    echo -e "\033[1;31m❌ Python not found in PATH\033[0m"
    echo -e "\033[1;33mInstall Python or add to PATH\033[0m"
    exit 1
fi

# 8. Verificar dependências
echo -e "\n\033[1;36m🔍 Checking dependencies...\033[0m"
if [ -f "backend/requirements.txt" ]; then
    echo -e "\033[1;32m✅ requirements.txt found\033[0m"
    read -p "Install/update dependencies? (yes/no): " install_deps
    if [ "$install_deps" = "yes" ]; then
        echo -e "\n\033[1;36m📦 Installing dependencies...\033[0m"
        cd backend
        $PYTHON_CMD -m pip install -r requirements.txt
        cd ..
        echo -e "\033[1;32m✅ Dependencies installed\033[0m"
    fi
fi

# 9. Executar seed script
echo -e "\n\033[1;36m🚀 Executing seed script...\033[0m"
echo "============================================================"

cd backend/scripts
$PYTHON_CMD seed_production_remote.py
exit_code=$?
cd ../..

if [ $exit_code -eq 0 ]; then
    echo -e "\n\033[1;32m✅ Seed completed successfully!\033[0m"
    echo -e "\n\033[1;36m🎯 Next steps:\033[0m"
    echo "  1. Open https://vivae-frontend.onrender.com"
    echo "  2. Login with your credentials"
    echo "  3. Navigate to Production → Planning"
    echo "  4. Verify demo data is present"
else
    echo -e "\n\033[1;31m❌ Seed failed with exit code: $exit_code\033[0m"
fi

echo ""
