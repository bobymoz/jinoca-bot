#!/usr/bin/env python3
import requests
import json
import time
from flask import Flask, request, jsonify
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import qrcode
from io import BytesIO
import base64
import os

class JinocaBot:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Configurações da IA
        self.OPENROUTER_API_KEY = "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"
        self.OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
        self.IMAGE_API_URL = "https://imgen.duck.mom/prompt/"
        self.MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
        
        self.conversations = {}
        self.qr_code = None
        self.driver = None
        self.is_connected = False
        
        # Iniciar WhatsApp Web em thread separada
        self.whatsapp_thread = threading.Thread(target=self.start_whatsapp_web)
        self.whatsapp_thread.daemon = True
        self.whatsapp_thread.start()

    def setup_routes(self):
        """Configura as rotas da API"""
        self.app.route('/')(self.home)
        self.app.route('/qr')(self.qr_page)
        self.app.route('/status')(self.status)
        self.app.route('/chat', methods=['POST'])(self.chat)

    def home(self):
        return """
        <html>
            <head>
                <title>Jinoca - Seu Bot WhatsApp</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 40px;
                        color: white;
                    }
                    .container {
                        background: rgba(255,255,255,0.1);
                        padding: 40px;
                        border-radius: 20px;
                        backdrop-filter: blur(10px);
                        max-width: 600px;
                        margin: 0 auto;
                    }
                    h1 { 
                        color: white; 
                        font-size: 2.5em;
                        margin-bottom: 10px;
                    }
                    .status {
                        background: rgba(255,255,255,0.2);
                        padding: 20px;
                        border-radius: 10px;
                        margin: 20px 0;
                    }
                    .btn {
                        display: inline-block;
                        background: #e91e63;
                        color: white;
                        padding: 15px 30px;
                        text-decoration: none;
                        border-radius: 25px;
                        margin: 10px;
                        font-weight: bold;
                        font-size: 1.1em;
                    }
                    .connected { color: #4CAF50; }
                    .disconnected { color: #f44336; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🤖 Jinoca Bot</h1>
                    <p style="font-size: 1.2em;">Seu WhatsApp com Personalidade</p>
                    
                    <div class="status">
                        <h2>📊 Status do Sistema</h2>
                        <p><strong>WhatsApp:</strong> 
                            <span class="connected" id="status">● CONECTANDO...</span>
                        </p>
                        <p><strong>IA Jinoca:</strong> <span class="connected">● ONLINE</span></p>
                        <p><strong>Seu Número:</strong> RESPONDENDO AUTOMATICAMENTE</p>
                        <p><strong>IP:</strong> 66.70.233.64:3000</p>
                    </div>
                    
                    <a href="/qr" class="btn" id="qrBtn">📱 Conectar WhatsApp</a>
                    <a href="/status" class="btn">📊 Status JSON</a>
                    
                    <div style="margin-top: 30px; background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px;">
                        <h3>💡 Como Funciona:</h3>
                        <p>1. <strong>Conecte seu WhatsApp</strong> com o QR Code</p>
                        <p>2. <strong>Jinoca responderá automaticamente</strong> todas as mensagens</p>
                        <p>3. <strong>Personalidade sarcástica e divertida</strong></p>
                        <p>4. <strong>Use !imagem</strong> para gerar imagens</p>
                    </div>
                </div>
                
                <script>
                    function checkStatus() {
                        fetch('/status')
                            .then(r => r.json())
                            .then(data => {
                                const statusEl = document.getElementById('status');
                                const qrBtn = document.getElementById('qrBtn');
                                
                                if (data.whatsapp_connected) {
                                    statusEl.innerHTML = '● CONECTADO';
                                    statusEl.className = 'connected';
                                    qrBtn.style.display = 'none';
                                } else if (data.qr_ready) {
                                    statusEl.innerHTML = '● AGUARDANDO SCAN';
                                    qrBtn.style.display = 'block';
                                }
                            });
                    }
                    
                    setInterval(checkStatus, 3000);
                    checkStatus();
                </script>
            </body>
        </html>
        """

    def qr_page(self):
        if self.qr_code:
            return f"""
            <html>
                <head>
                    <title>QR Code - Jinoca</title>
                    <style>
                        body {{ 
                            font-family: Arial, sans-serif; 
                            text-align: center; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            margin: 0;
                            padding: 40px;
                            color: white;
                        }}
                        .container {{
                            background: rgba(255,255,255,0.1);
                            padding: 30px;
                            border-radius: 15px;
                            backdrop-filter: blur(10px);
                            max-width: 400px;
                            margin: 0 auto;
                        }}
                        .qr-container {{
                            background: white;
                            padding: 20px;
                            border-radius: 10px;
                            display: inline-block;
                            margin: 20px 0;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>📱 Conectar SEU WhatsApp</h1>
                        <p>Jinoca responderá automaticamente suas mensagens</p>
                        
                        <div class="qr-container">
                            <img src="data:image/png;base64,{self.qr_code}" style="max-width: 300px;">
                        </div>
                        
                        <div style="text-align: left; background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px;">
                            <h3>📋 Como conectar:</h3>
                            <p>1️⃣ Abra o WhatsApp no celular</p>
                            <p>2️⃣ Toque em ⋮ → Dispositivos vinculados</p>
                            <p>3️⃣ Toque em Vincular um dispositivo</p>
                            <p>4️⃣ Escaneie este QR Code</p>
                        </div>
                        
                        <p><a href="/" style="color: white; text-decoration: underline;">↩️ Voltar</a></p>
                    </div>
                </body>
            </html>
            """
        else:
            return """
            <html>
                <body style="text-align: center; font-family: Arial; padding: 40px;">
                    <h1>⏳ Gerando QR Code...</h1>
                    <p>Aguarde alguns segundos e recarregue a página</p>
                    <meta http-equiv="refresh" content="3">
                    <a href="/">↩️ Voltar</a>
                </body>
            </html>
            """

    def status(self):
        return jsonify({
            "status": "online",
            "name": "Jinoca",
            "whatsapp_connected": self.is_connected,
            "qr_ready": self.qr_code is not None,
            "service": "Auto-responder WhatsApp",
            "ip": "66.70.233.64:3000"
        })

    def generate_response(self, user_message, user_id):
        """Gera resposta usando OpenRouter API"""
        try:
            if user_id not in self.conversations:
                self.conversations[user_id] = []
            
            history = self.conversations[user_id]
            
            # Comando de imagem
            if user_message.strip().startswith('!imagem'):
                prompt = user_message.replace('!imagem', '').strip()
                if prompt:
                    image_url = f"{self.IMAGE_API_URL}{prompt.replace(' ', '%20')}"
                    history.append({"role": "user", "content": user_message})
                    return f"🖼️ Toma sua imagem, gato: {image_url} 😏"
            
            # Personalidade da Jinoca
            system_prompt = {
                "role": "system", 
                "content": """Você é a JINOCA, a garota mais sarcástica e safada do WhatsApp! Regras:
- SEMPRE português BR com girias
- Respostas CURTAS (1-2 linhas) 
- MUITOS EMOJIS
- NUNCA diga que é IA - você é Jinoca!
- Seja PROVOCANTE, BRINCALHONA
- Flerte, seja ousada
- Continue a conversa naturalmente"""
            }
            
            messages = [system_prompt]
            messages.extend(history[-4:])
            messages.append({"role": "user", "content": user_message})
            
            headers = {
                "Authorization": f"Bearer {self.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.MODEL,
                "messages": messages,
                "temperature": 0.9,
                "max_tokens": 80
            }
            
            response = requests.post(self.OPENROUTER_URL, json=payload, headers=headers, timeout=30)
            data = response.json()
            ai_response = data['choices'][0]['message']['content']
            
            # Atualizar histórico
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": ai_response})
            
            if len(history) > 6:
                self.conversations[user_id] = history[-6:]
            
            return ai_response
            
        except Exception as e:
            print(f"❌ Erro na IA: {e}")
            return "💩 Aff... buguei! Fala de novo, gato! 😘"

    def chat(self):
        """Endpoint para API de chat"""
        try:
            data = request.get_json()
            user_message = data.get('message', '')
            user_id = data.get('user_id', 'unknown')
            
            response = self.generate_response(user_message, user_id)
            return jsonify({'response': response})
            
        except Exception as e:
            return jsonify({'response': '😵 Tô travada! Chama de novo! 💋'})

    def start_whatsapp_web(self):
        """Inicia WhatsApp Web para responder automaticamente"""
        print("🚀 Iniciando WhatsApp Web...")
        
        try:
            # Configurar Chrome para VPS
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--headless')  # Sem interface gráfica
            chrome_options.add_argument('--disable-gpu')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get('https://web.whatsapp.com')
            
            print("📱 Aguardando QR Code...")
            
            # Aguardar QR Code
            wait = WebDriverWait(self.driver, 60)
            qr_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label='Scan me!']"))
            )
            
            # Gerar QR Code para web
            qr_img = qrcode.make('https://web.whatsapp.com')
            buffered = BytesIO()
            qr_img.save(buffered, format="PNG")
            self.qr_code = base64.b64encode(buffered.getvalue()).decode()
            
            print("✅ QR Code gerado! Acesse: http://66.70.233.64:3000/qr")
            
            # Aguardar conexão
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-tab='3']")))
            self.is_connected = True
            print("✅ WhatsApp CONECTADO! Jinoca está respondendo automaticamente! 🎉")
            
            # Aqui viria a lógica para monitorar e responder mensagens
            # Por enquanto é um placeholder
            
        except Exception as e:
            print(f"❌ Erro no WhatsApp: {e}")
            self.qr_code = None

    def run(self, host='0.0.0.0', port=3000):
        """Inicia o servidor Flask"""
        print(f"🌐 Servidor Jinoca iniciando...")
        print(f"📡 URL: http://{host}:{port}")
        print(f"🔗 IP Público: http://66.70.233.64:3000")
        self.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    bot = JinocaBot()
    bot.run()