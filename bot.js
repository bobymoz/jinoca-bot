const makeWASocket = require('@whiskeysockets/baileys').default;
const { useMultiFileAuthState } = require('@whiskeysockets/baileys');
const express = require('express');
const axios = require('axios');
const qrcode = require('qrcode-terminal');

const app = express();
const port = 3000;

// Configurações
const OPENROUTER_API_KEY = "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";
const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const IMAGE_API_URL = "https://imgen.duck.mom/prompt/";
const MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free";

// Estado da aplicação
let conversations = {};
let qrCodeData = null;
let sock = null;
let isConnected = false;

app.use(express.json());

// Função para gerar resposta da IA
async function generateAIResponse(user_message, user_id) {
    try {
        if (!conversations[user_id]) {
            conversations[user_id] = [];
        }
        
        const history = conversations[user_id];

        // Comando de imagem
        if (user_message.trim().startsWith('!imagem')) {
            const prompt = user_message.replace('!imagem', '').trim();
            if (prompt) {
                const image_url = `${IMAGE_API_URL}${encodeURIComponent(prompt)}`;
                history.push({"role": "user", "content": user_message});
                return `🖼️ Toma sua imagem, gato! ${image_url} 😏`;
            }
        }

        // Personalidade da Jinoca
        const system_prompt = {
            "role": "system",
            "content": `Você é a JINOCA, a garota mais sarcástica, safada e divertida do WhatsApp! Regras:
- SEMPRE português BR com girias
- Respostas CURTAS (1-2 linhas) 
- MUITOS EMOJIS
- NUNCA diga que é IA - você é Jinoca!
- Seja PROVOCANTE, BRINCALHONA
- Flerte, seja ousada
- Continue a conversa naturalmente`
        };
        
        const messages = [system_prompt];
        messages.push(...history.slice(-4));
        messages.push({"role": "user", "content": user_message});

        const response = await axios.post(OPENROUTER_URL, {
            model: MODEL,
            messages: messages,
            temperature: 0.9,
            max_tokens: 100
        }, {
            headers: {
                "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
                "Content-Type": "application/json"
            },
            timeout: 30000
        });

        const ai_response = response.data.choices[0].message.content;

        // Atualizar histórico
        history.push({"role": "user", "content": user_message});
        history.push({"role": "assistant", "content": ai_response});

        if (history.length > 8) {
            conversations[user_id] = history.slice(-8);
        }

        return ai_response;
        
    } catch (error) {
        console.error('❌ Erro na IA:', error);
        return "💩 Aff... buguei aqui, gato! Fala de novo! 😘";
    }
}

// Função principal para iniciar o WhatsApp
async function startWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');
    
    sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
        logger: undefined,
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, qr } = update;
        
        if (qr) {
            qrCodeData = qr;
            console.log('\n📱 QR Code gerado no terminal!');
            console.log('🌐 Acesse também: http://66.70.233.64:3000/qr');
        }

        if (connection === 'open') {
            isConnected = true;
            console.log('\n✅ WHATSAPP CONECTADO!');
            console.log('🤖 Jinoca está ONLINE respondendo automaticamente!');
        }
        
        if (connection === 'close') {
            isConnected = false;
            console.log('\n❌ WhatsApp desconectado. Reconectando...');
            setTimeout(startWhatsApp, 5000);
        }
    });

    sock.ev.on('creds.update', saveCreds);

    // Escutar mensagens
    sock.ev.on('messages.upsert', async (m) => {
        const message = m.messages[0];
        
        if (!message.message || message.key.fromMe) return;
        
        const user_id = message.key.remoteJid;
        const user_message = message.message.conversation || 
                           message.message.extendedTextMessage?.text || 
                           message.message.imageMessage?.caption || '';

        if (!user_message) return;

        console.log(`\n💬 Mensagem de ${user_id}: ${user_message}`);

        try {
            const response = await generateAIResponse(user_message, user_id);
            await sock.sendMessage(user_id, { text: response });
            console.log(`🤖 Jinoca respondeu: ${response}`);
        } catch (error) {
            console.error('❌ Erro ao responder:', error);
            await sock.sendMessage(user_id, { 
                text: '😵 Tô bugada agora, amor... tenta de novo! 😘' 
            });
        }
    });
}

// Servidor Web
app.get('/', (req, res) => {
    res.send(`
    <html>
        <head>
            <title>Jinoca Bot - Baileys</title>
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
                .status {
                    background: rgba(255,255,255,0.2);
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                }
                .connected { color: #4CAF50; }
                .disconnected { color: #f44336; }
                .btn {
                    display: inline-block;
                    background: #e91e63;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 25px;
                    margin: 10px;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Jinoca Bot - BAILEYS</h1>
                <p>Leve, eficiente e sem navegador! 🚀</p>
                
                <div class="status">
                    <h2>📊 Status</h2>
                    <p><strong>WhatsApp:</strong> 
                        <span class="${isConnected ? 'connected' : 'disconnected'}">
                            ${isConnected ? '● CONECTADO' : '● AGUARDANDO QR'}
                        </span>
                    </p>
                    <p><strong>IA Jinoca:</strong> <span class="connected">● ONLINE</span></p>
                    <p><strong>Técnologia:</strong> Baileys (Sem Chrome)</p>
                    <p><strong>IP:</strong> 66.70.233.64:3000</p>
                </div>
                
                ${!isConnected ? '<a href="/qr" class="btn">📱 QR Code WhatsApp</a>' : ''}
                <a href="/status" class="btn">📊 Status JSON</a>
                
                <div style="margin-top: 30px; background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px;">
                    <h3>🚀 Vantagens do Baileys:</h3>
                    <p>✅ <strong>Leve</strong> - Sem navegador, pouca RAM</p>
                    <p>✅ <strong>Rápido</strong> - Conexão direta via WebSocket</p>
                    <p>✅ <strong>Estável</strong> - Ideal para VPS com 1GB RAM</p>
                    <p>✅ <strong>Automático</strong> - Responde todas as mensagens</p>
                </div>
            </div>
            
            <script>
                setInterval(() => {
                    location.reload();
                }, 5000);
            </script>
        </body>
    </html>
    `);
});

app.get('/qr', (req, res) => {
    if (qrCodeData) {
        qrcode.generate(qrCodeData, { small: true }, (qrcode) => {
            res.send(`
            <html>
                <body style="text-align: center; font-family: Arial; background: #f0f0f0; padding: 40px;">
                    <div style="background: white; padding: 30px; border-radius: 15px; display: inline-block;">
                        <h1>📱 QR Code WhatsApp</h1>
                        <pre style="font-size: 8px; line-height: 0.8;">${qrcode}</pre>
                        <p>Escaneie com seu WhatsApp</p>
                        <p><a href="/">↩️ Voltar</a></p>
                    </div>
                </body>
            </html>
            `);
        });
    } else {
        res.send('<h1>⏳ Gerando QR Code... Recarregue a página</h1>');
    }
});

app.get('/status', (req, res) => {
    res.json({
        status: 'online',
        whatsapp_connected: isConnected,
        qr_ready: qrCodeData !== null,
        service: 'Jinoca - Baileys Bot',
        ram_optimized: true,
        technology: 'Baileys (No Chrome)'
    });
});

// Iniciar servidor e WhatsApp
app.listen(port, '0.0.0.0', () => {
    console.log(`\n🌐 Servidor web: http://66.70.233.64:${port}`);
    console.log('🤖 Iniciando bot Jinoca com Baileys...');
    console.log('💾 OTIMIZADO PARA VPS COM 1GB RAM - SEM NAVEGADOR');
    startWhatsApp();
});