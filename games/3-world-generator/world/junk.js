const { sum } = require("../lib/math");

module.exports = {
    "@junk/strippedTriangle": function* ({ size }) {
        for (let i = 0; i < size; i++) {
            yield ({
                run: "fill",
                relativePoint: [i, 0, 0],
                relativeArea: [[0, 0, 0], [0, 0, i]],
                material: i % 2 === 0 ? "bricks" : "stone"
            });
        }
    },

    "@junk/setBlockExample": function* () {
        yield ({
            run: "setBlocks",
            blocks: [
                [
                    ["dirt", "stone"],
                    ["stone", "dirt"]
                ],
                [
                    ["stone", "dirt"],
                    ["dirt", "stone"]
                ]
            ]
        });
    },

    "@junk/4box": function* () {
        yield ({
            run: "fill",
            material: "air"
        });

        for (let x of [0, 2 / 3]) {
            for (let z of [0, 2 / 3]) {
                yield ({
                    run: "box",
                    areaScaler: [[x, 0, z], sum([x, 0, z], [1 / 3, 1, 1 / 3])]
                });
            }
        }
    },

    "@junk/demo": function* () {
        yield ({
            run: "fill",
            material: "air"
        });

        yield ({
            run: "fill",
            material: "stone",
            absoluteArea: [[190, 3, -200], [400, 3, 0]]
        });

        yield ({
            run: "@maze/main",
            relativePoint: [0, -1, 0],
            relativeArea: [[0, 0, 0], [20, 2, 20]],
            baseSize: 9,
            material: "bricks",
            paddingMaterial: "stone",
            randomizerSeed: 1
        });

        yield ({
            run: "@junk/4box",
            relativeArea: [[25, 0, 0], [45, 30, 20]],
            material: "glass"
        });

        yield ({
            run: "@junk/strippedTriangle",
            absolutePoint: [190, 4, -170],
            absoluteArea: [[190, 4, -170], [220, 100, -140]],
            size: 20
        });
    }
};