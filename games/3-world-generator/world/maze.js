module.exports = {
    "@maze/main": function* ({ baseSize, material, paddingMaterial, room = 1, border = 1, randomizerSeed }) {
        randomizerSeed = Math.abs(parseInt(randomizerSeed) || 0) + 1;

        room = room % 2 == 0 ? room - 1 : room;
        const isVisited = new Array(baseSize).fill().map(() => new Array(baseSize).fill(false));

        const block = room + border;
        const dataSize = baseSize * block + border;

        const blocks = new Array(dataSize).fill().map((_, x) => [
            new Array(dataSize).fill().map(
                (_, y) =>
                    (x < border ||
                        y < border ||
                        (x - border) % block >= room ||
                        (y - border) % block >= room) ? material : "air"
            )
        ]);

        function move(...args) {
            [x, y, xx, yy] = args.map(n => border + Math.floor(room / 2) + block * n);
            if (x === xx) {
                const min = Math.min(y, yy), max = Math.max(y, yy);
                for (let yyy = min; yyy <= max; yyy++) {
                    blocks[x][0][yyy] = "air";
                }
            } else {
                const min = Math.min(x, xx), max = Math.max(x, xx);
                for (let xxx = min; xxx <= max; xxx++) {
                    blocks[xxx][0][y] = "air";
                }
            }
        };

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
                ([xx, yy]) => xx >= 0 && yy >= 0 && xx < baseSize && yy < baseSize && !isVisited[xx][yy]
            );
            if (canVisit.length) {
                let n = Math.floor(canVisit.length * Math.abs(Math.sin(randomizerSeed++)));
                let [xx, yy] = canVisit[n];
                isVisited[xx][yy] = true;

                move(x, y, xx, yy);

                stack.push([x, y], [xx, yy]);
            }
        }

        blocks[0][0][1] = "air";
        blocks[dataSize - 1][0][dataSize - 2] = "air";

        yield ({
            run: "fill",
            relativeArea: [[0, 0, 0], [dataSize - 1, border - 1, dataSize - 1]],
            material: paddingMaterial
        });

        yield ({
            run: "setBlocks",
            blocks,
            relativePoint: [0, border, 0]
        });

        yield ({
            run: "setBlocks",
            blocks,
            relativePoint: [0, border + 1, 0]
        });
    }
};