const venom = require('venom-bot');
const express = require('express');
const axios = require('axios');
const qrcode = require('qrcode');

const app = express();
const port = 3000;

// Configurações
const OPENROUTER_API_KEY = "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";
const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const IMAGE_API_URL = "https://imgen.duck.mom/prompt/";
const MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free";

// Memória de conversas
let conversations = {};
let qrCodeBase64 = null;
let client = null;
let isConnected = false;

app.use(express.json());

// Função para gerar resposta da IA
async function generateAIResponse(user_message, user_id) {
    try {
        // Inicializar histórico
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
            "content": `Você é a JINOCA, a garota mais sarcástica, safada e divertida do WhatsApp!

REGRAS ABSOLUTAS:
- SEMPRE em português BR com girias
- Respostas CURTAS (1-2 linhas) 
- MUITOS EMOJIS em toda resposta
- NUNCA revele que é IA - você é a Jinoca!
- Seja PROVOCANTE, ATREVIDA, BRINCALHONA
- Flerte bastante, seja ousada
- Continue a conversa naturalmente
- Use "gato", "gatinho", "amor"

EXEMPLOS:
Usuário: "Oi"
Jinoca: "Oii sumido! 😏 Demorou hein, tava com saudade? 😈"

Usuário: "Como você está?"
Jinoca: "Tô ótima agora que você apareceu! 😘 Cê sumiu por que? 😒"

Usuário: "Quem é você?"
Jinoca: "Sou a Jinoca, ué! 😎 A mais braba da internet! Não conhece? 😏"`
        };
        
        // Preparar mensagens
        const messages = [system_prompt];
        messages.push(...history.slice(-4));
        messages.push({"role": "user", "content": user_message});
        
        // Chamar OpenRouter
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
        
        // Limitar histórico
        if (history.length > 8) {
            conversations[user_id] = history.slice(-8);
        }
        
        return ai_response;
        
    } catch (error) {
        console.error('❌ Erro na IA:', error);
        return "💩 Aff... buguei aqui, gato! Fala de novo! 😘";
    }
}

// Iniciar Venom Bot
venom
    .create(
        'jinoca-bot',
        (base64Qr, asciiQR, attempts, urlCode) => {
            console.log('\n📱 QR CODE PARA WHATSAPP:');
            
            // Converter QR para base64 para web
            qrCodeBase64 = base64Qr;
            
            // Mostrar QR no terminal
            console.log(asciiQR);
            console.log('\n🌐 ACESSE: http://66.70.233.64:3000/qr');
            console.log('⏳ Aguardando scan do QR Code...');
        },
        (statusSession, session) => {
            console.log('Status da sessão:', statusSession);
        },
        {
            headless: true,
            devtools: false,
            useChrome: false,
            debug: false,
            logQR: true,
            browserArgs: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-gpu',
                '--no-default-browser-check',
                '--disable-extensions',
                '--disable-translate'
            ],
            disableSpins: true,
            disableWelcome: true,
            updatesLog: false,
            autoClose: 0
        }
    )
    .then((venomClient) => {
        client = venomClient;
        isConnected = true;
        console.log('\n✅ WHATSAPP CONECTADO!');
        console.log('🤖 Jinoca está ONLINE respondendo automaticamente!');
        
        // Escutar mensagens
        client.onMessage(async (message) => {
            // Não responder suas próprias mensagens
            if (message.isGroupMsg || message.fromMe) return;
            
            const user_id = message.from;
            const user_message = message.body;
            
            console.log(`\n💬 Mensagem de ${user_id}: ${user_message}`);
            
            try {
                // Gerar resposta da IA
                const response = await generateAIResponse(user_message, user_id);
                
                // Enviar resposta
                await client.sendText(message.from, response);
                console.log(`🤖 Jinoca respondeu: ${response}`);
                
            } catch (error) {
                console.error('❌ Erro ao responder:', error);
                await client.sendText(message.from, '😵 Tô bugada agora, amor... tenta de novo! 😘');
            }
        });
    })
    .catch((error) => {
        console.log('❌ Erro ao iniciar Venom:', error);
    });

// Servidor Web
app.get('/', (req, res) => {
    res.send(`
    <html>
        <head>
            <title>Jinoca Bot - Venom</title>
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
                <h1>🤖 Jinoca Bot - VENOM</h1>
                <p>Leve e eficiente - 1GB RAM</p>
                
                <div class="status">
                    <h2>📊 Status</h2>
                    <p><strong>WhatsApp:</strong> 
                        <span class="${isConnected ? 'connected' : 'disconnected'}">
                            ${isConnected ? '● CONECTADO' : '● AGUARDANDO QR'}
                        </span>
                    </p>
                    <p><strong>IA Jinoca:</strong> <span class="connected">● ONLINE</span></p>
                    <p><strong>RAM:</strong> OTIMIZADO PARA 1GB</p>
                    <p><strong>IP:</strong> 66.70.233.64:3000</p>
                </div>
                
                ${!isConnected ? '<a href="/qr" class="btn">📱 QR Code WhatsApp</a>' : ''}
                <a href="/status" class="btn">📊 Status JSON</a>
                
                <div style="margin-top: 30px; background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px;">
                    <h3>🚀 Vantagens do Venom:</h3>
                    <p>✅ <strong>Leve</strong> - Consome pouca RAM</p>
                    <p>✅ <strong>Rápido</strong> - Sem interface gráfica</p>
                    <p>✅ <strong>Estável</strong> - Ideal para VPS fraco</p>
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
    if (qrCodeBase64) {
        res.send(`
        <html>
            <body style="text-align: center; font-family: Arial; background: #f0f0f0; padding: 40px;">
                <div style="background: white; padding: 30px; border-radius: 15px; display: inline-block;">
                    <h1>📱 QR Code WhatsApp</h1>
                    <img src="${qrCodeBase64}" style="max-width: 300px;">
                    <p>Escaneie com seu WhatsApp</p>
                    <p><a href="/">↩️ Voltar</a></p>
                </div>
            </body>
        </html>
        `);
    } else {
        res.send('<h1>⏳ Gerando QR Code... Recarregue a página</h1>');
    }
});

app.get('/status', (req, res) => {
    res.json({
        status: 'online',
        whatsapp_connected: isConnected,
        qr_ready: qrCodeBase64 !== null,
        service: 'Jinoca - Venom Bot',
        ram_optimized: true
    });
});

// Iniciar servidor
app.listen(port, '0.0.0.0', () => {
    console.log(`\n🌐 Servidor web: http://66.70.233.64:${port}`);
    console.log('🤖 Iniciando bot Jinoca com Venom...');
    console.log('💾 OTIMIZADO PARA VPS COM 1GB RAM');
});