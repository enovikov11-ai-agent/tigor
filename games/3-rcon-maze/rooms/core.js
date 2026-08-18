// https://gamedevelopment.tutsplus.com/tutorials/create-a-procedurally-generated-dungeon-cave-system--gamedev-10099

function* mazeGenerator(size = 10, room = 1, border = 1) {
    const block = room + border, dataSize = size * block + border,
        isVisited = new Array(size).fill().map(() => new Array(size).fill(false));
    yield ({
        type: 'setSize',
        x: dataSize,
        y: dataSize
    });

    for(let x = 0; x < dataSize; x++) {
        for(let y = 0; y < dataSize; y++) {
            yield ({
                type: 'setBlock',
                x,
                y,
                hasBlock: x < border || y < border || (x - border) % block >= room
                    || (y - border) % block >= room
            });
        }
    }

    function* move(...args) {
        [x, y, xx, yy] = args.map(n => border + Math.floor(room / 2) + block * n);
        if(x === xx) {
            const min = Math.min(y, yy), max = Math.max(y, yy);
            for(let yyy = min; yyy <= max; yyy++){
                yield ({
                    type: 'setBlock',
                    x,
                    y: yyy,
                    hasBlock: false
                });
            }
        }else {
          const min = Math.min(x, xx), max = Math.max(x, xx);
          for(let xxx = min; xxx <= max; xxx++){
            yield ({
                type: 'setBlock',
                x: xxx,
                y,
                hasBlock: false
            });
          }
        }
    }

    let stack = [[0, 0]];
    isVisited[0][0] = true;
    while (stack.length) {
      let [x, y] = stack.pop();
      const canVisit = [
        [x - 1, y],
        [x, y - 1],
        [x + 1, y],
        [x, y + 1]
      ].filter(([x, y]) => x >= 0 && y >= 0 && x < size && y < size && !isVisited[x][y]);
      if (canVisit.length) {
        let n = Math.floor(canVisit.length * Math.random());
        let [xx, yy] = canVisit[n];
        isVisited[xx][yy] = true;
        stack.push([x, y], [xx, yy]);
        yield* move(x, y, xx, yy); 
      }
    }
};

if(typeof module !== "undefined") {
    module.exports = { mazeGenerator };
}