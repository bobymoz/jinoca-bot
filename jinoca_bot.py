#!/usr/bin/env python3
import os
import json
import time
import requests
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

class JinocaBot:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Configurações
        self.OPENROUTER_API_KEY = "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"
        self.OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
        self.IMAGE_API_URL = "https://imgen.duck.mom/prompt/"
        self.MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
        
        self.conversations = {}
        self.qr_code = None
        self.driver = None
        
        # Iniciar WhatsApp em thread separada
        self.whatsapp_thread = threading.Thread(target=self.start_whatsapp)
        self.whatsapp_thread.daemon = True
        self.whatsapp_thread.start()

    def setup_routes(self):
        """Configura as rotas da API"""
        self.app.route('/')(self.home)
        self.app.route('/qr')(self.qr_page)
        self.app.route('/chat', methods=['POST'])(self.chat)
        self.app.route('/status')(self.status)

    def home(self):
        return """
        <html>
            <body style="text-align: center; font-family: Arial;">
                <h1>🤖 Bot Jinoca</h1>
                <p><a href="/qr">📱 Escanear QR Code</a></p>
                <p><a href="/status">📊 Status</a></p>
            </body>
        </html>
        """

    def qr_page(self):
        if self.qr_code:
            return f"""
            <html>
                <body style="text-align: center; font-family: Arial;">
                    <h1>📱 Escanear QR Code</h1>
                    <img src="data:image/png;base64,{self.qr_code}" style="max-width: 300px;">
                    <p>Abra WhatsApp > Configurações > Dispositivos vinculados</p>
                </body>
            </html>
            """
        else:
            return "<h1>⏳ Gerando QR Code... Recarregue a página.</h1>"

    def status(self):
        return jsonify({
            "status": "online",
            "name": "Jinoca",
            "qr_ready": self.qr_code is not None
        })

    def generate_response(self, user_message, user_id):
        """Gera resposta usando OpenRouter API"""
        try:
            # Inicializar histórico se necessário
            if user_id not in self.conversations:
                self.conversations[user_id] = []
            
            history = self.conversations[user_id]
            
            # Comando de imagem
            if user_message.strip().startswith('!imagem'):
                prompt = user_message.replace('!imagem', '').strip()
                if prompt:
                    image_url = f"{self.IMAGE_API_URL}{prompt.replace(' ', '%20')}"
                    history.append({"role": "user", "content": user_message})
                    history.append({"role": "assistant", "content": f"Imagem: {image_url}"})
                    return f"🖼️ Aqui sua imagem: {image_url}"
            
            # Prompt do sistema para personalidade
            system_prompt = {
                "role": "system", 
                "content": """Você é a Jinoca, uma garota extremamente arrogante, sarcástica, safada e brincalhona.
SEMPRE responda em português. Seja direta, curta e use emojis.
NUNCA revele que é uma IA. Você é a Jinoca!
Continue a conversa de onde parou. Seja provocante e divertida!"""
            }
            
            # Preparar mensagens
            messages = [system_prompt]
            messages.extend(history[-6:])  # Últimas 3 conversas
            messages.append({"role": "user", "content": user_message})
            
            # Fazer requisição para OpenRouter
            headers = {
                "Authorization": f"Bearer {self.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.MODEL,
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 150
            }
            
            response = requests.post(self.OPENROUTER_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            ai_response = data['choices'][0]['message']['content']
            
            # Atualizar histórico
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": ai_response})
            
            # Manter histórico limitado
            if len(history) > 10:
                self.conversations[user_id] = history[-10:]
            
            return ai_response
            
        except Exception as e:
            print(f"❌ Erro na IA: {e}")
            return "💩 Tô bugada agora, fala de novo?"

    def chat(self):
        """Endpoint para receber mensagens"""
        try:
            data = request.get_json()
            user_message = data.get('message', '')
            user_id = data.get('user_id', 'unknown')
            
            response = self.generate_response(user_message, user_id)
            return jsonify({'response': response})
            
        except Exception as e:
            print(f"❌ Erro no chat: {e}")
            return jsonify({'response': '😵 Tô travada, tenta de novo!'})

    def start_whatsapp(self):
        """Inicia o WhatsApp Web via Selenium"""
        print("🚀 Iniciando WhatsApp...")
        
        try:
            # Configurar Chrome
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--headless')  # Remover para ver o navegador
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get('https://web.whatsapp.com')
            
            print("📱 Aguardando QR Code...")
            
            # Aguardar QR Code aparecer
            wait = WebDriverWait(self.driver, 60)
            qr_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label='Scan me!']"))
            )
            
            # Gerar QR Code para web
            qr_img = qrcode.make('https://web.whatsapp.com')
            buffered = BytesIO()
            qr_img.save(buffered, format="PNG")
            self.qr_code = base64.b64encode(buffered.getvalue()).decode()
            
            print("✅ QR Code gerado! Acesse: http://142.93.190.157:3000/qr")
            
            # Aguardar login
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-tab='3']")))
            print("✅ WhatsApp conectado! Jinoca está online! 🎉")
            
            # Manter sessão ativa
            while True:
                time.sleep(10)
                
        except Exception as e:
            print(f"❌ Erro no WhatsApp: {e}")
            self.qr_code = None

    def run(self, host='0.0.0.0', port=3000):
        """Inicia o servidor Flask"""
        print(f"🌐 Servidor iniciando em http://{host}:{port}")
        self.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    bot = JinocaBot()
    bot.run()