#!/bin/bash
echo "🚀 Instalando Bot Jinoca..."

# Atualizar sistema
apt update && apt upgrade -y

# Instalar Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Instalar PM2 globalmente
npm install -g pm2

# Instalar dependências do projeto
npm install

echo "✅ Instalação concluída!"
echo "📱 Para iniciar: npm start"
echo "🌐 Acesse: http://66.70.233.64:3000"