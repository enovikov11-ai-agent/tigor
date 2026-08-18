const { mazeGenerator } = require('./core'), maze = mazeGenerator();

const main = renderMaze;

const Rcon = require("rcon");
const conn = new Rcon("localhost", 8088, "321321");

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

async function cleanup(send) {
    const { x, y, z } = base;
    for(let dx = 0; dx < 40; dx++){
        for(let dy = 0; dy < 40; dy++){
            for(let dz = 0; dz < 40; dz++){
                await send(`/setblock ${x + dx} ${z + dz} ${y + dy} minecraft:air`);
            }
        }
    }
}

  
async function renderMaze(send) {
    const { x, y, z } = base;

    for(let {x: dx, y: dy, hasBlock, type} of maze) {
        if(type !== "setBlock") {
            return;
        }

        for(let dz = 0; dz < 3; dz++) {
            let blockType = dz === 0 || hasBlock ? "stone" : "air";
            await send(`/setblock ${x + dx} ${z + dz} ${y + dy} minecraft:${blockType}`);
        }
    }
  }