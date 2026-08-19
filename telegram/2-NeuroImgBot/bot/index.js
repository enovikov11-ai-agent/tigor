const { stringify } = require('yaml');

console.yaml = function (object) {
    console.log(stringify(object) + '\n');
}

const express = require('express'), bodyParser = require('body-parser'), secrets = require('../secrets.json'),
    { sendMessage, setWebhook } = require('./telegram'), { parseRequest } = require('./query'),
    { clearWatchdog, ensureRunning } = require('./yandex-cloud-manager'), app = express();

app.use(bodyParser.json());

let tasks = [], longpollTriggers = [];

app.get(`/${secrets.SERVER_SECRET}/get-task-longpoll`, async (req, res) => {
    if (tasks.length) {
        const task = tasks.shift();
        console.yaml({ timeLongpolled: Date.now(), task });
        res.json(task);
        clearWatchdog();
        return;
    }

    longpollTriggers.push(() => { try { res.json(null) } catch (e) { } });
});

app.get(`/${secrets.SERVER_SECRET}/notify-stopped`, async (req, res) => { res.send('OK'); });

app.post(`/${secrets.SERVER_SECRET}/tg-callback`, async (req, res) => {
    res.json({ ok: true });
    const update = req.body, message = update?.message, chatId = message?.chat?.id, messageId = message?.message_id,
        request = message?.text || message?.caption, photo = message?.photo, parsedRequest = parseRequest(request, Boolean(photo), message?.reply_to_message?.from?.username === 'NeuroImgBot');

    console.yaml(update);

    try {
        if (!secrets.ALLOWED_GUIDS.includes(chatId)) {
            await sendMessage({ chatId, text: `Ask @enovikov11 for access` });
            return;
        }

        if (message?.from?.is_bot || !parsedRequest) {
            return;
        }

        const task = {
            ...parsedRequest,
            chatId,
            messageId
        };

        if (photo) {
            const { file_id: fileId, file_unique_id: fileUniqueId } = photo[photo.length - 1];
            task.requestPhoto = { fileId, fileUniqueId };
        }

        const { message_id: enqueuedMessageId } = await sendMessage({ chatId, replyToMessageid: messageId, disableNotification: true, text: `Enqueued, tasks before: ${tasks.length}` });
        task.enqueuedMessageId = enqueuedMessageId;

        tasks.push(task);
        console.yaml({ timeEnqueued: Date.now(), task });
        longpollTriggers.forEach(trigger => trigger());
        ensureRunning();
    } catch (e) {
        console.error(e);
    }
});

async function main() {
    await setWebhook({ url: `${secrets.SERVER_BASE}${secrets.SERVER_SECRET}/tg-callback`, allowed_updates: ['message', 'edited_message'] });
    app.listen(8000);
}

main().catch(console.error);
