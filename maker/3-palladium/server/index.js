const secret = process.env.SECRET;

if (!secret) {
  process.exit();
}

const express = require('express');
const http = require('http');
const ws = require('ws');
const app = express();
const server = http.createServer(app);
const WebSocketServer = ws.Server;
const wss = new WebSocketServer({server, path: '/' + secret});

app.use(express.static('../www'));

app.get('/', (req, res) => {
  res.send('ok');
});

server.listen(80);

let receiver;

wss.on('connection', client => client.on('message', message => {
  try {
    receiver.send(message);
  } catch (e) {
    console.error(e);
  }

  if(message === "1") {
    receiver = client;
  }
}));