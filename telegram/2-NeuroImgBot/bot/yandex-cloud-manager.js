const { promisify } = require('node:util'), exec = promisify(require('node:child_process').exec);

const CHECKING_INTERVAL = 2 * 60 * 1000, WATCHDOG_INTERVAL = 12 * 60 * 1000,
    CIRCLE_BUFFER_SIZE = 24 * 60 / 2, MAX_ACTIVE_ALLOWED = CIRCLE_BUFFER_SIZE / 8,
    WORKER_NAME = 'neuroimgbot-worker', execConfig = { timeout: 5 * 60 * 1000 };

let lastActiveAt = 0, activityCircleBuffer = new Array(CIRCLE_BUFFER_SIZE).fill(false), activityI = 0;

function isQuotaExceeded() {
    return activityCircleBuffer.filter(Boolean).length > MAX_ACTIVE_ALLOWED;
}

async function getStatus() {
    const { stdout } = await exec(`yc compute instance get ${WORKER_NAME} --format json`, execConfig);

    return JSON.parse(stdout).status;
}

async function start() {
    await exec(`yc compute instance start ${WORKER_NAME} --format json`, execConfig);
}

async function stop() {
    await exec(`yc compute instance stop ${WORKER_NAME} --format json`, execConfig);
}

async function check() {
    const status = await getStatus(), isWatchdogTriggered = lastActiveAt + WATCHDOG_INTERVAL < Date.now();

    activityCircleBuffer[activityI] = status !== 'STOPPED';
    activityI = (activityI + 1) % CIRCLE_BUFFER_SIZE;

    if (status === 'RUNNING' && (isQuotaExceeded() || isWatchdogTriggered)) {
        await stop();
    }
}

function clearWatchdog() {
    lastActiveAt = Date.now();
}

function ensureRunning() {
    console.yaml({
        used: activityCircleBuffer.filter(Boolean).length,
        of: MAX_ACTIVE_ALLOWED,
        period: CIRCLE_BUFFER_SIZE
    });

    if (isQuotaExceeded()) {
        return;
    }

    lastActiveAt = Date.now();
    start().catch(() => null);
}

setInterval(() => check().catch(console.error), CHECKING_INTERVAL);

module.exports = { clearWatchdog, ensureRunning };
