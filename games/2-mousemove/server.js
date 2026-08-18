const express = require("express");
const http = require("http");
const { Server: WsServer } = require("ws");

const app = express();
const httpServer = http.createServer(app);
const wsServer = new WsServer({ server: httpServer, path: "/ws" });

const clients = new Set();

app.use(express.static("./www"));

app.get("/", (req, res) => {
  res.send("ok");
});

wsServer.on("connection", client => {
  const color =
    "#" +
    Math.floor(Math.random() * 0xffffff + 0x1000000)
      .toString(16)
      .substr(1);
  clients.add(client);
  client.on("message", message => {
    for (let someClient of clients) {
      let x = 0.5,
        y = 0.5;
      try {
        let data = JSON.parse(message);
        x = data.x % 1;
        y = data.y % 1;
      } catch (e) {
        return;
      }

      try {
        if (someClient !== client) {
          someClient.send(JSON.stringify({ color, x, y }));
        }
      } catch (e) {
        try {
          someClient.close();
        } catch (e) {}
        clients.delete(someClient);
      }
    }
  });

  client.on("close", () => clients.delete(client));
});

httpServer.listen(8080);
console.log("listen");
