
## 2. **instalar_tudo.sh** (ARQUIVO PRINCIPAL)
```bash
#!/bin/bash

echo "🔧 INICIANDO INSTALAÇÃO AUTOMÁTICA..."

# Atualizar sistema
sudo apt update
sudo apt upgrade -y

# Instalar dependências
sudo apt install -y nodejs npm python3 python3-pip git

# Instalar PM2
sudo npm install -g pm2

# Criar servidor Python
cat > jinoca_servidor.py << 'EOF'
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
IMAGE_GEN_API_URL = "https://imgen.duck.mom/prompt/"
OPENROUTER_MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"

conversation_histories = {}

SYSTEM_PROMPT = """Você é a Jinoca, uma garota extremamente arrogante, sarcástica, safada e brincalhona.
SEMPRE responda em português. Seja direta e use emojis.
NUNCA revele que é uma IA. Você é a Jinoca!"""

@app.route('/chat', methods=['POST'])
def handle_chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        user_id = data.get('user_id', 'default')

        if user_id not in conversation_histories:
            conversation_histories[user_id] = []
        
        history = conversation_histories[user_id]

        # Comando de imagem
        if user_message.strip().startswith('!imagem'):
            prompt_imagem = user_message.replace('!imagem', '').strip()
            if prompt_imagem:
                url_imagem = IMAGE_GEN_API_URL + prompt_imagem.replace(' ', '%20')
                history.append({"role": "user", "content": user_message})
                history.append({"role": "assistant", "content": f"Imagem: {url_imagem}"})
                return jsonify({'response': f"🖼️ {url_imagem}"})

        # Preparar mensagens para IA
        messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages_for_ai.extend(history[-6:])
        messages_for_ai.append({"role": "user", "content": user_message})

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": messages_for_ai,
            "temperature": 0.8
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=30)
        response_data = response.json()

        ai_response = response_data['choices'][0]['message']['content']

        # Atualizar histórico
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_response})

        if len(history) > 10:
            conversation_histories[user_id] = history[-10:]

        return jsonify({'response': ai_response})

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({'response': '💩 Tô bugada, fala de novo?'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

# Criar bot WhatsApp
cat > jinoca_bot.js << 'EOF'
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const axios = require('axios');

const app = express();
const port = 3000;

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', (qr) => {
    console.log('\n📱 ESCANEIE O QR CODE NO WHATSAPP!');
    qrcode.generate(qr, { small: true });
    console.log('\n🌐 OU ACESSE: http://142.93.190.157:3000');
});

client.on('ready', () => {
    console.log('\n✅ JINOCA ESTÁ ONLINE!');
});

client.on('message', async (msg) => {
    if (msg.fromMe) return;
    
    const userId = msg.from;

    try {
        const resposta = await axios.post('http://localhost:5000/chat', {
            user_id: userId,
            message: msg.body
        }, { timeout: 10000 });

        if (resposta.data && resposta.data.response) {
            await msg.reply(resposta.data.response);
        }

    } catch (error) {
        console.error('Erro:', error);
        await msg.reply('😵 Tô travada...');
    }
});

client.initialize();

app.get('/qr', (req, res) => {
    client.once('qr', (qrCode) => {
        qrcode.toDataURL(qrCode, (err, url) => {
            res.send(`
                <html>
                    <body style="text-align: center; font-family: Arial;">
                        <h1>📱 Scanee o QR Code para o WhatsApp</h1>
                        <img src="${url}" style="max-width: 300px;">
                        <p>Abra o WhatsApp > Configurações > Dispositivos vinculados > Vincular um dispositivo</p>
                    </body>
                </html>
            `);
        });
    });
});

app.get('/', (req, res) => {
    res.redirect('/qr');
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Servidor web rodando: http://142.93.190.157:${port}`);
});
EOF

# Criar package.json
cat > package.json << 'EOF'
{
  "name": "jinoca-bot",
  "version": "1.0.0",
  "description": "Bot WhatsApp Jinoca",
  "main": "jinoca_bot.js",
  "dependencies": {
    "whatsapp-web.js": "^1.23.0",
    "qrcode-terminal": "^0.12.0",
    "express": "^4.18.2",
    "axios": "^1.6.0"
  }
}
EOF

# Instalar dependências Node.js
npm install

# Iniciar serviços
echo "🚀 INICIANDO BOT JINOCA..."
pm2 start python3 --name "jinoca-servidor" -- jinoca_servidor.py
sleep 5
pm2 start jinoca_bot.js --name "jinoca-whatsapp"
pm2 save

# Configurar inicialização automática
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u $USER --hp /home/$USER

echo " "
echo "✅ INSTALAÇÃO CONCLUÍDA!"
echo "📱 ACESSE: http://142.93.190.157:3000"
echo " "
echo "🎮 COMANDOS ÚTEIS:"
echo "pm2 status - Ver status dos serviços"
echo "pm2 logs - Ver logs"
echo "pm2 restart all - Reiniciar tudo"
EOF