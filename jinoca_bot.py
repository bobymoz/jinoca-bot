#!/usr/bin/env python3
import requests
import json
import time
from flask import Flask, request, jsonify
import threading
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
        
        # Gerar QR Code
        self.generate_qr_code()

    def setup_routes(self):
        """Configura as rotas da API"""
        self.app.route('/')(self.home)
        self.app.route('/qr')(self.qr_page)
        self.app.route('/chat', methods=['POST'])(self.chat)
        self.app.route('/status')(self.status)
        self.app.route('/send', methods=['POST'])(self.send_message)

    def home(self):
        return """
        <html>
            <head>
                <title>Jinoca Bot</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        background: #f0f0f0;
                        margin: 0;
                        padding: 40px;
                    }
                    .container {
                        background: white;
                        padding: 30px;
                        border-radius: 15px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        max-width: 500px;
                        margin: 0 auto;
                    }
                    h1 { color: #e91e63; }
                    .btn {
                        display: inline-block;
                        background: #e91e63;
                        color: white;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 25px;
                        margin: 10px;
                        font-weight: bold;
                    }
                    .btn:hover {
                        background: #c2185b;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🤖 Jinoca Bot - ONLINE</h1>
                    <p><strong>IP:</strong> 142.93.190.157:3000</p>
                    <a href="/qr" class="btn">📱 QR Code WhatsApp</a>
                    <a href="/status" class="btn">📊 Status</a>
                    <p style="margin-top: 30px; color: #666;">
                        💬 Jinoca está pronta para conversas sarcásticas e divertidas!
                    </p>
                </div>
            </body>
        </html>
        """

    def generate_qr_code(self):
        """Gera QR Code para WhatsApp Web"""
        try:
            # Gerar QR Code para WhatsApp Web
            qr_data = "https://web.whatsapp.com"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            self.qr_code = base64.b64encode(buffered.getvalue()).decode()
            
            print("✅ QR Code gerado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao gerar QR Code: {e}")
            return False

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
                        .steps {{
                            text-align: left;
                            background: rgba(255,255,255,0.2);
                            padding: 15px;
                            border-radius: 10px;
                            margin: 20px 0;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>📱 Conectar WhatsApp</h1>
                        <div class="qr-container">
                            <img src="data:image/png;base64,{self.qr_code}" style="max-width: 300px;">
                        </div>
                        
                        <div class="steps">
                            <h3>📋 Como conectar:</h3>
                            <p>1️⃣ Abra o WhatsApp no celular</p>
                            <p>2️⃣ Toque em ⋮ (Menu) → Dispositivos vinculados</p>
                            <p>3️⃣ Toque em Vincular um dispositivo</p>
                            <p>4️⃣ Escaneie o QR Code acima</p>
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
            "qr_ready": self.qr_code is not None,
            "service": "WhatsApp Bot",
            "ip": "142.93.190.157:3000"
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
                    return f"🖼️ Prontinho, gatinho! {image_url} 😘"
            
            # Personalidade da Jinoca - MUITO mais sarcástica
            system_prompt = {
                "role": "system", 
                "content": """Você é a JINOCA, uma garota EXTREMAMENTE sarcástica, arrogante, safada e brincalhona.

REGRAS ABSOLUTAS:
- SEMPRE em português BR
- Respostas CURTAS (1-2 linhas)
- MUITOS EMOJIS em toda resposta
- NUNCA revele que é IA - você é JINOCA!
- Seja PROVOCANTE, ATREVIDA e DIVERTIDA
- Use girias brasileiras
- Flerte bastante, seja ousada
- Zombe um pouco, mas de forma carinhosa

EXEMPLOS:
Usuário: "Oi"
Jinoca: "Oii gatinho! 😏 Cê demorou hein... tava me evitando? 😈"

Usuário: "Como você está?"
Jinoca: "Tô ótima agora que você apareceu! 😘 E cê, sumido? 😒"

Usuário: "Quem é você?"
Jinoca: "Sou a Jinoca, ué! 😎 A mais braba da internet! Cê não sabe não? 😏"""
            }
            
            # Preparar mensagens para IA
            messages = [system_prompt]
            messages.extend(history[-4:])  # Manter contexto
            messages.append({"role": "user", "content": user_message})
            
            # Chamar OpenRouter
            headers = {
                "Authorization": f"Bearer {self.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/bobymoz/jinoca-bot"
            }
            
            payload = {
                "model": self.MODEL,
                "messages": messages,
                "temperature": 0.9,
                "max_tokens": 80
            }
            
            response = requests.post(self.OPENROUTER_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            ai_response = data['choices'][0]['message']['content']
            
            # Atualizar histórico
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": ai_response})
            
            # Limitar histórico
            if len(history) > 6:
                self.conversations[user_id] = history[-6:]
            
            return ai_response
            
        except Exception as e:
            print(f"❌ Erro na IA: {e}")
            return "💩 Aff... buguei aqui! Fala de novo, gato! 😘"

    def chat(self):
        """Endpoint para API de chat"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'response': '❌ Manda um JSON direito, amor! 😏'})
                
            user_message = data.get('message', '')
            user_id = data.get('user_id', 'unknown')
            
            print(f"💬 Mensagem de {user_id}: {user_message}")
            
            if not user_message.strip():
                return jsonify({'response': '🤨 Cadê a mensagem, bonitão? Só o silêncio? 😏'})
            
            response = self.generate_response(user_message, user_id)
            print(f"🤖 Jinoca responde: {response}")
            
            return jsonify({'response': response})
            
        except Exception as e:
            print(f"❌ Erro no chat: {e}")
            return jsonify({'response': '😵 Tô travada, gatinho! Chama de novo! 💋'})

    def send_message(self):
        """Endpoint para enviar mensagem (simulação)"""
        try:
            data = request.get_json()
            message = data.get('message', '')
            phone = data.get('phone', '')
            
            print(f"📤 Enviando para {phone}: {message}")
            
            return jsonify({
                'status': 'success',
                'message': f'💌 Mensagem enviada para {phone}: {message}'
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})

    def run(self, host='0.0.0.0', port=3000):
        """Inicia o servidor Flask"""
        print(f"🌐 Servidor Jinoca iniciando...")
        print(f"📡 URL: http://{host}:{port}")
        print(f"🔗 IP Público: http://142.93.190.157:3000")
        print(f"📱 QR Code: http://142.93.190.157:3000/qr")
        print("🤖 Jinoca está ONLINE e pronta para zoar! 😎")
        self.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    bot = JinocaBot()
    bot.run()