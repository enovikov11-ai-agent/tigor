const { spawnSync } = require('child_process'), { writeFileSync } = require('fs'),
    fetch = require('node-fetch'),
    { checkMountPaths, connectPath, telegramApiToken, telegramChatId } = require('./config.json'),
    timeout = 20000;

function run(command) {
    const [name, ...args] = command.split(' '),
        { stdout } = spawnSync(name, args, { timeout });
    return stdout.toString().replace(/[ ]+/g, ' ');
}

function getIO() {
    try {
        const [, cpu, devices] = run('iostat').replace(/,/g, '.').split('\n\n'),
            devicesList = devices.split('\n').splice(1).map(line => line.split(' '));

        return {
            cpuLoadPerc: (100 - +(cpu.split('\n')[1].split(' ')[6])).toFixed(2),
            readMBpS: (devicesList.map(line => +line[2]).reduce((a, b) => a + b) / 1000).toFixed(2),
            writeMBpS: (devicesList.map(line => +line[3]).reduce((a, b) => a + b) / 1000).toFixed(2)
        };
    } catch (e) {
        return null;
    }
}

function getMem() {
    try {
        return {
            freeMemGB: (run('free').replace(/,/g, '.').split('\n')[1].split(' ')[6] / 1000000).toFixed(2)
        }
    } catch (e) {
        return null;
    }
}

function getConnections() {
    try {
        return {
            connections: [...run('chia show -c').matchAll(/\d+\.\d+\.\d+\.\d+/g)].map(name => name[0])
        }
    } catch (e) {
        return null;
    }
}

function getStatus() {
    try {
        const status = run('chia show -s');

        return {
            isSynced: status.includes('Current Blockchain Status: Full Node Synced'),
            blockchainHeight: status.match(/Height: (\d+)/)[1]
        };
    } catch (e) {
        return null;
    }
}

function getMountStatus() {
    try {
        const mounts = run('df');

        return {
            isMounted: checkMountPaths.every(path => mounts.includes(path))
        };
    } catch (e) {
        return null;
    }
}

function getFarmStatus() {
    try {
        const info = Object.fromEntries(run('chia farm summary').split('\n').map(line => line.split(': ')));

        return {
            isFarming: info['Farming status'] === 'Farming',
            totalFarmed: info['Total chia farmed'],
            plotCount: info['Plot count'],
            networkSpace: info['Estimated network space'],
            timeToWin: info['Expected time to win']
        }
    } catch (e) {
        return null;
    }
}

function updateConnect(ips = []) {
    writeFileSync(connectPath, ips.map(ip => `chia show -a ${ip}:8444`).join('\n'));
}

function iterate() {
    const stats = {
        ...getFarmStatus(),
        ...getIO(),
        ...getMem(),
        ...getConnections(),
        ...getStatus(),
        ...getMountStatus()
    }, text = (stats.totalFarmed === '0.0' || !stats.totalFarmed ? '' : 'УРА!!! НАМАЙНИЛ!!!\n\n') +
        (stats.isFarming ? '' : 'Ошибка: farming не запущен\n\n') +
        (stats.isSynced ? '' : 'Ошибка: нода не синхронизирована\n\n') +
        (stats.isMounted ? '' : 'Ошибка: отвалились маунты\n\n') +
        `Количество плотов: ${stats.plotCount}\nВыигрыш через: ${stats.timeToWin}\n` +
        `Нафармил: ${stats.totalFarmed} XCH\nЕмкость сети: ${stats.networkSpace}\n\n` +
        `Соединений: ${stats.connections.length}\nБлоков: ${stats.blockchainHeight}\n\n` +
        `Загрузка процессора: ${stats.cpuLoadPerc}%\nСвободно памяти: ${stats.freeMemGB} GB\n` +
        `Запись: ${stats.writeMBpS} MB/s\nЧтение: ${stats.readMBpS} MB/s`;

    updateConnect(stats.connections);

    fetch(`https://api.telegram.org/bot${telegramApiToken}/sendMessage`, {
        method: 'POST',
        body: JSON.stringify({ chat_id: telegramChatId, text }),
        headers: { 'Content-Type': 'application/json' },
        timeout,
        redirect: 'error'
    });
}

iterate();
setInterval(iterate, 4 * 60 * 60 * 1000);
