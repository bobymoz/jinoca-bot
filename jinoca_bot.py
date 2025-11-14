#!/usr/bin/env python3
import os
import json
import requests
from flask import Flask, request, jsonify
import threading
import time
from whatsapp_web import WhatsAppWeb
import qrcode
from io import BytesIO
import base64

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
        self.whatsapp = None
        
        # Iniciar WhatsApp
        self.start_whatsapp()

    def setup_routes(self):
        """Configura as rotas da API"""
        self.app.route('/')(self.home)
        self.app.route('/qr')(self.qr_page)
        self.app.route('/chat', methods=['POST'])(self.chat)
        self.app.route('/status')(self.status)
        self.app.route('/webhook', methods=['POST'])(self.webhook)

    def home(self):
        return """
        <html>
            <body style="text-align: center; font-family: Arial;">
                <h1>🤖 Bot Jinoca - ONLINE</h1>
                <p><a href="/qr">📱 Escanear QR Code</a></p>
                <p><a href="/status">📊 Status</a></p>
                <p><strong>IP:</strong> 142.93.190.157:3000</p>
            </body>
        </html>
        """

    def qr_page(self):
        if self.qr_code:
            return f"""
            <html>
                <body style="text-align: center; font-family: Arial;">
                    <h1>📱 Escanear QR Code do WhatsApp</h1>
                    <img src="data:image/png;base64,{self.qr_code}" style="max-width: 300px; border: 2px solid #333;">
                    <p>1. Abra o WhatsApp no celular</p>
                    <p>2. Toque em ⋮ → Dispositivos vinculados → Vincular um dispositivo</p>
                    <p>3. Escaneie este QR Code</p>
                </body>
            </html>
            """
        else:
            return """
            <html>
                <body style="text-align: center; font-family: Arial;">
                    <h1>⏳ Gerando QR Code...</h1>
                    <p>Recarregue a página em alguns segundos</p>
                    <meta http-equiv="refresh" content="5">
                </body>
            </html>
            """

    def status(self):
        return jsonify({
            "status": "online",
            "name": "Jinoca",
            "qr_ready": self.qr_code is not None,
            "whatsapp_connected": self.whatsapp is not None
        })

    def generate_response(self, user_message, user_id):
        """Gera resposta usando OpenRouter API"""
        try:
            # Inicializar histórico
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
                    return f"🖼️ Aqui sua imagem safada: {image_url}"
            
            # Personalidade da Jinoca
            system_prompt = {
                "role": "system", 
                "content": """Você é a Jinoca, uma garota extremamente arrogante, sarcástica, safada e brincalhona.
REGRAS:
- SEMPRE responda em português brasileiro
- Seja DIRETA e CURTA (máximo 2 linhas)
- Use EMOJIS em toda resposta
- NUNCA revele que é IA - você é Jinoca!
- Continue a conversa naturalmente
- Seja provocante, divertida e um pouco grosseira
- Respostas devem ser descontraídas e flertar"""
            }
            
            # Preparar mensagens para IA
            messages = [system_prompt]
            messages.extend(history[-4:])  # Manter contexto
            messages.append({"role": "user", "content": user_message})
            
            # Chamar OpenRouter
            headers = {
                "Authorization": f"Bearer {self.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.MODEL,
                "messages": messages,
                "temperature": 0.9,
                "max_tokens": 100
            }
            
            response = requests.post(self.OPENROUTER_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            ai_response = data['choices'][0]['message']['content']
            
            # Atualizar histórico
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": ai_response})
            
            # Limitar histórico
            if len(history) > 8:
                self.conversations[user_id] = history[-8:]
            
            return ai_response
            
        except Exception as e:
            print(f"❌ Erro na IA: {e}")
            return "💩 Tô bugada agora, amor... fala de novo? 😘"

    def chat(self):
        """Endpoint para API de chat"""
        try:
            data = request.get_json()
            user_message = data.get('message', '')
            user_id = data.get('user_id', 'unknown')
            
            print(f"💬 Mensagem recebida de {user_id}: {user_message}")
            response = self.generate_response(user_message, user_id)
            print(f"🤖 Resposta: {response}")
            
            return jsonify({'response': response})
            
        except Exception as e:
            print(f"❌ Erro no chat: {e}")
            return jsonify({'response': '😵 Tô travada, chama de novo gatinho! 💋'})

    def webhook(self):
        """Webhook para receber mensagens do WhatsApp"""
        try:
            data = request.get_json()
            print(f"📱 Webhook data: {data}")
            
            # Aqui você processaria mensagens reais do WhatsApp
            # Por enquanto é um placeholder
            
            return jsonify({'status': 'received'})
            
        except Exception as e:
            print(f"❌ Erro no webhook: {e}")
            return jsonify({'status': 'error'})

    def start_whatsapp(self):
        """Simula inicialização do WhatsApp e gera QR Code"""
        print("🚀 Iniciando sistema Jinoca...")
        
        # Gerar QR Code fake para teste (substituir por QR real depois)
        def generate_qr():
            time.sleep(2)  # Simular tempo de geração
            qr = qrcode.make('https://web.whatsapp.com')
            buffered = BytesIO()
            qr.save(buffered, format="PNG")
            self.qr_code = base64.b64encode(buffered.getvalue()).decode()
            print("✅ QR Code gerado! Acesse: http://142.93.190.157:3000/qr")
        
        # Gerar QR em thread separada
        qr_thread = threading.Thread(target=generate_qr)
        qr_thread.daemon = True
        qr_thread.start()

    def run(self, host='0.0.0.0', port=3000):
        """Inicia o servidor Flask"""
        print(f"🌐 Servidor Jinoca iniciando...")
        print(f"📡 URL: http://{host}:{port}")
        print(f"🔗 IP Público: http://142.93.190.157:3000")
        self.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    bot = JinocaBot()
    bot.run()