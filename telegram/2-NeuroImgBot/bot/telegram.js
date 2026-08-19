const fetch = require('node-fetch'), secrets = require('../secrets.json');
const botBase = `https://api.telegram.org/bot${secrets.TELEGRAM_API_KEY}/`;

async function apiRaw({ method, body, headers }) {
    await new Promise(res => setTimeout(res, 100));

    const { result, ok, error } = await fetch(`${botBase}${method}`, {
        method: 'POST', body, headers, timeout: 60000, redirect: 'error'
    }).then(res => res.json());

    if (!ok) {
        throw new Error(JSON.stringify({ method, data, result, error }));
    }

    return result;
}

async function api(method, data) {
    return await apiRaw({
        method,
        body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json' }
    });
}

async function sendMessage({ text, chatId, replyToMessageid, disableNotification = false }) {
    return await api('sendMessage', {
        chat_id: chatId,
        text,
        reply_to_message_id: replyToMessageid,
        disable_notification: disableNotification
    });
}

async function setWebhook({ url, allowedUpdates }) {
    return await api('setWebhook', { url, allowed_updates: allowedUpdates });
}

module.exports = { sendMessage, setWebhook };
