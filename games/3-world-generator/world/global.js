module.exports = {
    world: function* () {
        yield ({
            run: "@junk/demo",
            absolutePoint: [190, 4, -200],
            absoluteArea: [[190, 3, -200], [400, 100, 0]],
            material: "bricks"
        });
    },

    box: function* ({ absoluteArea: [[ax1, ay1, az1], [ax2, ay2, az2]] }) {
        yield ({ absoluteArea: [[ax1, ay1, az1], [ax2, ay2, az1]], run: "fill" });
        yield ({ absoluteArea: [[ax1, ay1, az2], [ax2, ay2, az2]], run: "fill" });
        yield ({ absoluteArea: [[ax1, ay1, az1], [ax2, ay1, az2]], run: "fill" });
        yield ({ absoluteArea: [[ax1, ay2, az1], [ax2, ay2, az2]], run: "fill" });
        yield ({ absoluteArea: [[ax1, ay1, az1], [ax1, ay2, az2]], run: "fill" });
        yield ({ absoluteArea: [[ax2, ay1, az1], [ax2, ay2, az2]], run: "fill" });
    },

    setBlocks: function* ({ blocks }) {
        for (let x = 0; x < blocks.length; x++) {
            const yzBlocks = blocks[x];
            for (let y = 0; y < yzBlocks.length; y++) {
                const zBlocks = yzBlocks[y];
                for (let z = 0; z < zBlocks.length; z++) {
                    const material = zBlocks[z];
                    if (material) {
                        yield ({
                            run: "fill",
                            relativeArea: [[x, y, z], [x, y, z]],
                            material
                        });
                    }
                }
            }
        }
    }
}