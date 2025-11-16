#!/bin/bash
echo "🚀 Instalando Bot Jinoca com Venom..."

# Atualizar sistema
apt update && apt upgrade -y

# Instalar Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Instalar dependências do sistema para Venom
apt install -y libnss3-dev libatk-bridge2.0-dev libx11-xcb-dev libxcomposite-dev libxdamage-dev libxrandr-dev libgbm-dev libxss-dev

# Instalar dependências do projeto
npm install

echo "✅ Instalação concluída!"
echo "📱 Para iniciar: npm start"
echo "🌐 Acesse: http://66.70.233.64:3000"
echo "💾 OTIMIZADO PARA 1GB RAM"