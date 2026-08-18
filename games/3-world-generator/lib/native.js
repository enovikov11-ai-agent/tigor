const Rcon = require("rcon");
const conn = new Rcon(process.env.RCON_HOST, process.env.RCON_PORT, process.env.RCON_PASSWORD);

let onAuth, authWait = new Promise(res => { onAuth = res }), onResponse = () => { };

conn.on("auth", () => onAuth())
    .on("response", () => onResponse())
    .on("error", console.error);
conn.connect();

module.exports = {
    async fill({ absoluteArea: [[ax1, ay1, az1], [ax2, ay2, az2]], material }) {
        if (!material) {
            return;
        }

        if (Number(process.env.DEBUG) === 1) {
            console.log("fill", arguments[0]);
        }

        await authWait;

        for (let x = Math.min(ax1, ax2); x <= Math.max(ax1, ax2); x += 16) {
            for (let z = Math.min(az1, az2); z <= Math.max(az1, az2); z += 16) {

                await new Promise(res => {
                    onResponse = res;
                    conn.send(`forceload add ${x} ${z}`);
                });

                await new Promise(res => {
                    onResponse = res;
                    conn.send(`fill ${x} ${Math.min(ay1, ay2)} ${z} ${Math.min(x + 16, Math.max(ax1, ax2))} ${Math.max(ay1, ay2)} ${Math.min(z + 16, Math.max(az1, az2))} minecraft:${material}`);
                });

                await new Promise(res => {
                    onResponse = res;
                    conn.send(`forceload remove ${x} ${z}`);
                });
            }
        }
    },
    async close() {
        await authWait;

        conn.disconnect();
    }
}
