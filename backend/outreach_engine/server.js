const { default: makeWASocket, DisconnectReason, fetchLatestBaileysVersion, initAuthCreds, BufferJSON, proto } = require('@whiskeysockets/baileys');
const pino = require('pino');
const QRCode = require('qrcode');
const axios = require('axios');
const FormData = require('form-data');
const express = require('express');
const Redis = require('ioredis');

const TG_BOT_TOKEN = '7989031523:AAG06PB2n4nrYkkThYXwczdpngMzL9RabqA';
const TG_CHAT_ID = '5547351734';
const PORT = 8085;
const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379/1';

const app = express();
app.use(express.json());

let sock = null;
let isConnected = false;
let lastQr = null;
let hasSentInitialQr = false;
let lastTelegramSendTime = 0;
let reconnectAttempts = 0;

const redis = new Redis(REDIS_URL, {
    maxRetriesPerRequest: null,
    enableReadyCheck: false
});

redis.on('error', (err) => console.error('Redis error:', err.message));
redis.on('connect', () => console.log('Connected to Redis for WhatsApp session persistence.'));

async function useRedisAuthState(redisClient, sessionKey = 'baileys_auth') {
    const writeData = async (data, key) => {
        try {
            await redisClient.set(`${sessionKey}:${key}`, JSON.stringify(data, BufferJSON.replacer));
        } catch (e) {
            console.error(`Error saving auth key ${key}:`, e.message);
        }
    };

    const readData = async (key) => {
        try {
            const data = await redisClient.get(`${sessionKey}:${key}`);
            if (data) {
                return JSON.parse(data, BufferJSON.reviver);
            }
        } catch (error) {
            console.error(`Error reading ${key} from Redis:`, error.message);
        }
        return null;
    };

    const removeData = async (key) => {
        try {
            await redisClient.del(`${sessionKey}:${key}`);
        } catch (error) {
            console.error(`Error removing ${key} from Redis:`, error.message);
        }
    };

    const creds = (await readData('creds')) || initAuthCreds();

    return {
        state: {
            creds,
            keys: {
                get: async (type, ids) => {
                    const data = {};
                    await Promise.all(
                        ids.map(async (id) => {
                            let value = await readData(`${type}-${id}`);
                            if (type === 'app-state-sync-key' && value) {
                                value = proto.Message.AppStateSyncKeyData.fromObject(value);
                            }
                            data[id] = value;
                        })
                    );
                    return data;
                },
                set: async (data) => {
                    const tasks = [];
                    for (const category in data) {
                        for (const id in data[category]) {
                            const value = data[category][id];
                            const key = `${category}-${id}`;
                            tasks.push(value ? writeData(value, key) : removeData(key));
                        }
                    }
                    await Promise.all(tasks);
                },
            },
        },
        saveCreds: () => writeData(creds, 'creds'),
        clearState: async () => {
            const keys = await redisClient.keys(`${sessionKey}:*`);
            if (keys.length > 0) {
                await redisClient.del(...keys);
            }
        }
    };
}

async function sendTelegramPhoto(imageBuffer, caption) {
    const now = Date.now();
    if (now - lastTelegramSendTime < 30000 && hasSentInitialQr) {
        console.log('Debouncing Telegram photo send...');
        return;
    }
    lastTelegramSendTime = now;

    try {
        const form = new FormData();
        form.append('chat_id', TG_CHAT_ID);
        form.append('caption', caption);
        form.append('parse_mode', 'HTML');
        form.append('photo', imageBuffer, { filename: 'whatsapp_qr.png', contentType: 'image/png' });

        await axios.post('https://api.telegram.org/bot' + TG_BOT_TOKEN + '/sendPhoto', form, {
            headers: form.getHeaders(),
            timeout: 20000
        });
        hasSentInitialQr = true;
        console.log('✅ QR Code image sent to Telegram (Single send, no loop)!');
    } catch (err) {
        console.error('Error sending photo to Telegram:', err.message);
    }
}

async function sendTelegramText(text) {
    try {
        await axios.post('https://api.telegram.org/bot' + TG_BOT_TOKEN + '/sendMessage', {
            chat_id: TG_CHAT_ID,
            text: text,
            parse_mode: 'HTML'
        }, { timeout: 10000 });
    } catch (err) {
        console.error('Error sending text to Telegram:', err.message);
    }
}

async function startWhatsApp() {
    try {
        const { state, saveCreds, clearState } = await useRedisAuthState(redis, 'baileys_session');
        const { version } = await fetchLatestBaileysVersion();

        sock = makeWASocket({
            version,
            logger: pino({ level: 'silent' }),
            printQRInTerminal: false,
            auth: state,
            browser: ['Mujeeb Outreach Engine', 'Chrome', '120.0.0'],
            connectTimeoutMs: 60000,
            defaultQueryTimeoutMs: 60000,
            keepAliveIntervalMs: 10000,
            emitOwnEvents: false,
            fireInitQueries: true,
            generateHighQualityLinkPreview: true,
            syncFullHistory: false
        });

        sock.ev.on('creds.update', saveCreds);

        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                lastQr = qr;
                console.log('⚡️ QR Code updated in memory.');
                if (!hasSentInitialQr) {
                    try {
                        const qrBuffer = await QRCode.toBuffer(qr, { width: 450, margin: 2 });
                        const caption = (
                            '📲 <b>SCANNEZ CE QR CODE (WHATSAPP OUTREACH)</b>\n\n' +
                            '1. Ouvrez <b>WhatsApp</b> sur votre téléphone\n' +
                            '2. Allez dans <b>Appareils connectés</b> > <b>Connecter un appareil</b>\n' +
                            '3. Scannez ce QR Code ci-dessus.\n\n' +
                            '⚡️ <i>Valable pour l\'outreach sans frais Meta !</i>'
                        );
                        await sendTelegramPhoto(qrBuffer, caption);
                    } catch (qrErr) {
                        console.error('Failed to generate QR buffer:', qrErr.message);
                    }
                }
            }

            if (connection === 'close') {
                isConnected = false;
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
                console.log('Connection closed, statusCode:', statusCode, 'reconnecting:', shouldReconnect);

                if (shouldReconnect) {
                    reconnectAttempts++;
                    const delay = Math.min(5000 * Math.pow(1.5, reconnectAttempts - 1), 60000);
                    console.log(`Reconnecting in ${delay / 1000}s (Attempt ${reconnectAttempts})...`);
                    setTimeout(startWhatsApp, delay);
                } else {
                    console.log('Session logged out or expired. Clearing Redis session state...');
                    await clearState();
                    hasSentInitialQr = false;
                    lastQr = null;
                    reconnectAttempts = 0;
                    setTimeout(startWhatsApp, 3000);
                }
            } else if (connection === 'open') {
                isConnected = true;
                lastQr = null;
                hasSentInitialQr = true;
                reconnectAttempts = 0;
                console.log('🎉 WhatsApp Connected successfully with Redis session persistence!');
                await sendTelegramText('🎉 <b>WHATSAPP CONNECTÉ AVEC SUCCÈS !</b>\n\nVotre moteur d\'outreach privé est prêt (Session persistée dans Redis).');
            }
        });
    } catch (err) {
        console.error('Error starting WhatsApp client:', err);
        setTimeout(startWhatsApp, 5000);
    }
}

// HTTP API Endpoints
app.get('/status', (req, res) => {
    res.json({ connected: isConnected, hasQr: !!lastQr });
});

app.get('/qr', async (req, res) => {
    if (isConnected) {
        return res.json({ status: 'connected', message: 'WhatsApp is already connected!' });
    }
    if (lastQr) {
        const qrBuffer = await QRCode.toBuffer(lastQr, { width: 450, margin: 2 });
        lastTelegramSendTime = 0;
        await sendTelegramPhoto(qrBuffer, '📲 <b>Voici votre QR Code WhatsApp (Demandé)</b>');
        return res.json({ status: 'sent', message: 'QR Code sent to Telegram!' });
    }
    res.json({ status: 'pending', message: 'Generating QR code, please wait...' });
});

app.post('/send-text', async (req, res) => {
    try {
        const { phone, message } = req.body;
        const cleanPhone = phone.replace(/[^0-9]/g, '');
        const jid = cleanPhone + '@s.whatsapp.net';

        if (!isConnected || !sock) {
            return res.status(503).json({ error: 'WhatsApp is not connected' });
        }

        const result = await sock.sendMessage(jid, { text: message });
        res.json({ success: true, result });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/send-media', async (req, res) => {
    try {
        const { phone, mediaUrl, caption, mediaType } = req.body;
        const cleanPhone = phone.replace(/[^0-9]/g, '');
        const jid = cleanPhone + '@s.whatsapp.net';

        if (!isConnected || !sock) {
            return res.status(503).json({ error: 'WhatsApp is not connected' });
        }

        const messagePayload = mediaType === 'video' 
            ? { video: { url: mediaUrl }, caption: caption, mimetype: 'video/mp4' }
            : { image: { url: mediaUrl }, caption: caption };

        const result = await sock.sendMessage(jid, messagePayload);
        res.json({ success: true, result });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, '0.0.0.0', () => {
    console.log('🚀 Outreach Engine listening on port ' + PORT);
    startWhatsApp();
});

