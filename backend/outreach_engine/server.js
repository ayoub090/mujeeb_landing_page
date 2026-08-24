const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const pino = require('pino');
const QRCode = require('qrcode');
const axios = require('axios');
const FormData = require('form-data');
const express = require('express');
const path = require('path');
const fs = require('fs');

const TG_BOT_TOKEN = '7989031523:AAG06PB2n4nrYkkThYXwczdpngMzL9RabqA';
const TG_CHAT_ID = '5547351734';
const PORT = 8085;

const app = express();
app.use(express.json());

let sock = null;
let isConnected = false;
let lastQr = null;
let hasSentInitialQr = false; // ANTI-SPAM: only send once on startup!
let lastTelegramSendTime = 0;

async function sendTelegramPhoto(imageBuffer, caption) {
    const now = Date.now();
    // Strict cooldown: max 1 photo every 30 seconds
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
    const authDir = path.join(__dirname, 'auth_info_baileys');
    const { state, saveCreds } = await useMultiFileAuthState(authDir);
    const { version } = await fetchLatestBaileysVersion();

    sock = makeWASocket({
        version,
        logger: pino({ level: 'silent' }),
        printQRInTerminal: false,
        auth: state,
        browser: ['Mujeeb Outreach Engine', 'Chrome', '120.0.0']
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            lastQr = qr;
            console.log('⚡️ QR Code updated in memory.');
            // Only auto-send to Telegram ONCE on startup
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
            console.log('Connection closed, reconnecting:', shouldReconnect);
            if (shouldReconnect) {
                setTimeout(startWhatsApp, 5000);
            } else {
                console.log('Session logged out. Clean auth folder to restart.');
            }
        } else if (connection === 'open') {
            isConnected = true;
            lastQr = null;
            hasSentInitialQr = true;
            console.log('🎉 WhatsApp Connected successfully via Baileys!');
            await sendTelegramText('🎉 <b>WHATSAPP CONNECTÉ AVEC SUCCÈS !</b>\n\nVotre moteur d\'outreach privé est prêt.');
        }
    });
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
        // Force sending when manually requested
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

app.listen(PORT, () => {
    console.log('🚀 Outreach Engine listening on http://127.0.0.1:' + PORT);
    startWhatsApp();
});
