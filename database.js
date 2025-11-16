const sqlite3 = require('sqlite3');
const { open } = require('sqlite');

let db;

/**
 * Inicializa o banco de dados e cria a tabela se não existir.
 */
async function initDb() {
    db = await open({
        filename: './chat_history.db', // Arquivo do banco de dados
        driver: sqlite3.Database
    });

    await db.exec(`
        CREATE TABLE IF NOT EXISTS messages (
            jid TEXT NOT NULL,
            message_id TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    `);
    
    await db.exec(`CREATE INDEX IF NOT EXISTS jid_timestamp ON messages (jid, timestamp);`);
    
    console.log('Banco de dados SQLite conectado e pronto.');
}

/**
 * Adiciona uma mensagem ao histórico.
 */
async function addMessage(jid, message_id, role, content) {
    if (!db) await initDb();
    
    try {
        await db.run(
            'INSERT INTO messages (jid, message_id, role, content) VALUES (?, ?, ?, ?)',
            [jid, message_id, role, content]
        );
    } catch (error) {
        console.error('Erro ao salvar mensagem no DB:', error.message);
    }
}

/**
 * Busca o histórico de conversa para um JID (ID de chat).
 */
async function getHistory(jid, limit = 10) {
    if (!db) await initDb();
    
    // Busca as últimas 'limit' mensagens, da mais antiga para a mais nova
    const messages = await db.all(
        'SELECT role, content FROM (SELECT * FROM messages WHERE jid = ? ORDER BY timestamp DESC LIMIT ?) ORDER BY timestamp ASC',
        [jid, limit]
    );
    
    return messages;
}

module.exports = { initDb, addMessage, getHistory };