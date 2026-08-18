// deno run --allow-all aio.js

import { TextLineStream } from "jsr:@std/streams/text-line-stream";

function clientMain() {
    const SCALE = 10, COLS = 100, ROWS = 61;

    const canvas = document.createElement("canvas");
    canvas.width = COLS * SCALE;
    canvas.height = ROWS * SCALE;
    canvas.style.imageRendering = "pixelated";
    document.body.appendChild(canvas);

    const ctx = canvas.getContext("2d", { alpha: false });
    ctx.fillStyle = "#000000";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const statDiv = document.createElement("div");
    statDiv.style.fontSize = "20px";
    statDiv.innerText = "move mouse";
    document.body.appendChild(statDiv);

    document.addEventListener("mousemove", (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (x >= 0 && x < canvas.width && y >= 0 && y < canvas.height) {
            const col = Math.floor(x / SCALE);
            const row = Math.floor(y / SCALE);
            const freq = row * COLS + col;

            if (freq in frequencyMaxs) {
                const pct = Math.floor(100 * (frequencyMaxs[freq] - min) / (max - min));
                statDiv.innerText = `${freq}MHz ${frequencyMaxs[freq].toFixed(2)}dBFS ${pct}%`;
            }
        }
    });

    window.ws = new WebSocket(location.href.replace(/^http/, "ws"));

    let frequencyMaxs = {}, min = -60, max = -59, msgs = 0;

    window.ws.onmessage = ({ data }) => {
        const values = data.split(","), freqStart = parseInt(values[0]);

        for (let i = 0; i < 5; i++) {
            const freq = freqStart + i, value = parseFloat(values[i + 1]);

            frequencyMaxs[freq] = (freq in frequencyMaxs) ? Math.max(frequencyMaxs[freq], value) : value;

            const color = Math.floor(255 * (frequencyMaxs[freq] - min) / (max - min));
            ctx.fillStyle = `rgb(${color}, ${color}, ${color})`;
            ctx.fillRect((freq % COLS) * SCALE, Math.floor(freq / COLS) * SCALE, SCALE, SCALE);
        }

        msgs++;

        if (msgs > 1200) {
            msgs = 0;
            min = Math.min(...Object.values(frequencyMaxs));
            max = Math.max(...Object.values(frequencyMaxs));
        }
    };

    window.ws.onclose = window.ws.onerror = () => {
        window.ws.onclose = window.ws.onerror = () => { };
        setTimeout(initWs, 3000);
    };
}

let currentSocket = null;

Deno.serve({ port: 8080 }, req => {
    if (req.headers.get("upgrade") === "websocket") {
        const { socket, response } = Deno.upgradeWebSocket(req);

        socket.onopen = () => {
            if (currentSocket && currentSocket.readyState === currentSocket.OPEN) {
                currentSocket.close();
            }
            currentSocket = socket;
        };

        socket.onclose = socket.onerror = () => {
            if (currentSocket === socket) {
                currentSocket = null;
            }
        };

        return response;
    }

    return new Response(`<!DOCTYPE html><html><head><meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>html, body { margin: 0; padding: 0; width: 100%; }</style></head>
        <body><script>${clientMain};clientMain();</script></body></html>`,
        { status: 200, headers: new Headers({ "content-type": "text/html", "cache-control": "no-store" }) });
});

async function streamLines() {
    const lines = new Deno.Command("hackrf_sweep", {
        args: ["-f", "10:5990", "-w", "1000000", "-l", "16", "-g", "24"],
        stdout: "piped",
        stderr: "inherit",
    }).spawn().stdout.pipeThrough(new TextDecoderStream()).pipeThrough(new TextLineStream());

    // date, time, start, end, width, n, v1, v2, v3, v4, v5
    for await (const line of lines) {
        const parts = line.split(", ");
        if (parts.length != 11) { throw new Error("Invariant violation"); }

        if (currentSocket && currentSocket.readyState === currentSocket.OPEN) {
            currentSocket.send([parts[2].slice(0, -6), ...parts.slice(-5)].join(","));
        }
    }
}

streamLines();
