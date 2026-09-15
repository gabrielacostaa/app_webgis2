#!/bin/bash

echo "Iniciando configuração do Geoportal WebGIS..."

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual (venv)..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências do Flask..."
pip install -r requirements.txt

# Inicializar Banco de Dados
echo "Inicializando banco de dados..."
python init_db.py

# Iniciar o servidor web
echo "==================================================="
echo "Iniciando o Servidor Flask..."
echo "Acesse no seu navegador: http://127.0.0.1:5001"
echo "Contas de teste:"
echo "Admin: admin / Admin@123"
echo "Org: org / Org@123"
echo "User: user / User@123"
echo "==================================================="
python app.py
