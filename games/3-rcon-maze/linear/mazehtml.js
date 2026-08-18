function Maze(Projector, size = 12, ...args) {
  const isVisited = new Array(size)
      .fill()
      .map(() => new Array(size).fill(false)),
    projector = new Projector(size, ...args);

  let stack = [[0, 0]];
  isVisited[0][0] = true;
  while (stack.length) {
    let [x, y] = stack.pop();
    const canVisit = [
      [x - 1, y],
      [x, y - 1],
      [x + 1, y],
      [x, y + 1]
    ].filter(
      ([xx, yy]) =>
        xx >= 0 && yy >= 0 && xx < size && yy < size && !isVisited[xx][yy]
    );
    if (canVisit.length) {
      let n = Math.floor(canVisit.length * Math.random());
      let [xx, yy] = canVisit[n];
      isVisited[xx][yy] = true;
      projector.move(x, y, xx, yy);
      stack.push([x, y], [xx, yy]);
    }
  }

  return projector;
}

function ProjectorRoomTunnel(size, room = 3, border = 2) {
  const block = room + border;
  this.dataSize = size * block + border;
  this.data = new Array(this.dataSize)
    .fill()
    .map((_, x) =>
      new Array(this.dataSize)
        .fill()
        .map(
          (_, y) =>
            x < border ||
            y < border ||
            (x - border) % block >= room ||
            (y - border) % block >= room
        )
    );

  this.move = (...args) => {
      [x, y, xx, yy] = args.map(n => border + Math.floor(room / 2) + block * n);
      if(x === xx) {
          const min = Math.min(y, yy), max = Math.max(y, yy);
          for(let yyy = min; yyy <= max; yyy++){
              this.data[x][yyy] = false;
          }
      }else {
        const min = Math.min(x, xx), max = Math.max(x, xx);
        for(let xxx = min; xxx <= max; xxx++){
            this.data[xxx][y] = false;
        }
      }
  };
}

let maze = new Maze(ProjectorRoomTunnel, 6);
maze.needCleanup = false;

if (typeof window !== "undefined") {
  const div = document.createElement("div");

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  div.appendChild(canvas);
  document.body.appendChild(div);
  const pixelSize = 20;
  canvas.width = canvas.height = pixelSize * maze.dataSize;

  render();

  function render() {
    for (let xx = 0; xx < maze.dataSize; xx++) {
      for (let yy = 0; yy < maze.dataSize; yy++) {
        const color = (maze.data[xx][yy] && "#000000") || "#ffffff";
        ctx.beginPath();
        ctx.rect(pixelSize * xx, pixelSize * yy, pixelSize, pixelSize);
        ctx.fillStyle = color;
        ctx.fill();
      }
    }
  }
} else {
  module.exports = maze;
}
