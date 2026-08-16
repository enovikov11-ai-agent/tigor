const { readdirSync, createWriteStream } = require('fs'), { spawn } = require('child_process'),
    { poolKey, farmerKey, workers, outputs, logsPath } = require('./config.json');

let availableOutputs = outputs.map(({ path, maxCount }) =>
    ({ path, freeCount: maxCount - readdirSync(path).length }));

function maybeAcquireOutputPath() {
    availableOutputs = availableOutputs.filter(({ freeCount }) => freeCount > 0);
    if (availableOutputs.length === 0) { return null; }

    const item = availableOutputs[Math.floor(availableOutputs.length * Math.random())];
    item.freeCount--;
    return item.path;
}

async function runPlotting({ tempPath, outputPath, workerName }) {
    const outputStream = createWriteStream(`${logsPath}/${workerName}-${Date.now()}.log`),
        plotter = spawn('chia', ['plots', 'create', '-k', '32', '-t', tempPath, '-d', outputPath, '-f', farmerKey, '-p', poolKey], { detached: false });

    plotter.stdout.pipe(outputStream);
    plotter.stderr.pipe(outputStream);
    await new Promise(res => plotter.on('close', res));
}

workers.forEach(async ({ tempPath, name }) => {
    let outputPath;
    while (outputPath = maybeAcquireOutputPath()) {
        await runPlotting({ tempPath, outputPath, workerName: name });
    }
});
