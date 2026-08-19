function getNeedRunning() {
    return true;
}

let quotaInfo = [{
    validUntil: 0,
    secondsLeft: 0,
    startedAt: null,
    needApiDelay: false,
    needCheckFast: false
}];

function onNewTask() {
    for (let i = 0; i < quotaInfo.length; i++) {
        if (canWorkerGetTasks(i)) {
            if (quotaInfo[i].startedAt === null) {
                quotaInfo[i].needCheckFast = true;
            }

            break;
        }
    }
}

function onWorkerStop(workerId) {
    if (!quotaInfo[+workerId]) {
        return;
    }

    quotaInfo[+workerId].needApiDelay = true;
    quotaInfo[+workerId].needCheckFast = true;
}

function canWorkerGetTasks(workerId) {
    if (!quotaInfo[+workerId]) {
        return false;
    }

    const { validUntil, secondsLeft, startedAt } = quotaInfo[+workerId];
    const runningNow = startedAt === null ? 0 : (Date.now() - startedAt);

    return validUntil > Date.now() && (secondsLeft - runningNow) > 0;
}

function updateQuotas(quotas) {
    try {
        const quotasJson = JSON.parse(quotas);
        if (!Array.isArray(quotasJson) || quotasJson.length !== quotaInfo.length
            || quotasJson.some(q => typeof q.validUntil !== "string" || isNaN(+new Date(q.validUntil))
                || typeof q.secondsLeft !== "number" || q.secondsLeft < 0 || q.secondsLeft > 300_000)) {
            return 'bad quotas';
        }

        for (let i = 0; i < quotasJson.length; i++) {
            quotaInfo[i].validUntil = +new Date(quotasJson[i].validUntil);
            quotaInfo.secondsLeft = quotasJson.secondsLeft;
        }
    } catch (e) {
        return 'bad quotas';
    }
}

function needWorkerToBeRunning(workerId) {
    if (!getNeedRunning()) {
        return false;
    }

    for (let i = 0; i < workerId; i++) {
        if (canWorkerGetTasks(i)) {
            return false;
        }
    }

    return true;
}

async function workerChore(workerId) {
    const quota = quotaInfo[workerId];

    while (true) {
        for (let i = 0; i < 20 && !quota.needCheckFast && !quota.needApiDelay; i++) {
            await new Promise(res => setTimeout(res, 100));
        }

        quota.needCheckFast = false;
        if (quota.needApiDelay) {
            await new Promise(res => setTimeout(res, 2000));
        }

        // get state until RUNNING or STOPPED, if !needWorkerToBeRunning, change
    }
}

quotaInfo.forEach((_, i) => workerChore(i));
