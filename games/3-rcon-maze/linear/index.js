const Rcon = require("rcon");
const conn = new Rcon("localhost", 10000, "321321");

let onResponse = () => {};

conn
  .on("auth", () => {
    (async () => {
      await main(async data => {
        conn.send(data);
        await new Promise(res => (onResponse = res));
      });

      conn.disconnect();
    })();
  })
  .on("response", () => onResponse());

conn.connect();

const base = {
  x: 150,
  y: 70,
  z: 70
};

const main = renderMaze;

const {dataSize, data, needCleanup} = require('./mazehtml');

async function renderMaze(send) {
  const { x, y, z } = base;
  for (let dx = 0; dx < dataSize; dx++) {
    for (let dy = 0; dy < dataSize; dy++) {
      for (let dz = 0; dz < 3; dz++) {
        let type = dz === 0 || data[dx][dy] ? "stone" : "air";
        if(needCleanup){
          type = 'air';
        }
        await send(`/setblock ${x + dx} ${z + dz} ${y + dy} minecraft:${type}`);
      }
    }
  }
}