

const N = getN(), SIZE = N ** 4, SWAPS = buildSwaps(), CHECKS = buildChecks();

function getN() {
    const N = +(new URLSearchParams(location.search).get("size") || "4");

    return Math.max(3, Math.min(7, N));
}

function vec2id([x, y, z, w]) {
    return x + N * (y + N * (z + N * w));
}

function forEachVec(callback) {
    for (let x = 0; x < N; x++)
        for (let y = 0; y < N; y++)
            for (let z = 0; z < N; z++)
                for (let w = 0; w < N; w++)
                    callback([x, y, z, w]);
}

function buildSwaps() {
    const axes = 'XYZW', swaps = {}, pairs = [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]];

    for (let [a, b] of pairs) {
        const swap = swaps[axes[a] + axes[b]] = new Array(SIZE);

        forEachVec(([x, y, z, w]) => {
            const fromVec = [x, y, z, w], toVec = [x, y, z, w];

            toVec[a] = fromVec[b];
            toVec[b] = fromVec[a];

            swap[vec2id(fromVec)] = vec2id(toVec);
        });
    }

    const XY2ZW = new Array(SIZE);
    forEachVec(([x, y, z, w]) => XY2ZW[vec2id([x, y, z, w])] = vec2id([z, w, x, y]));

    return { XY2ZW, ...swaps };
}

function buildChecks() {
    const checks = [], options = ["u", "d", ...Array.from({ length: N }, (_, i) => i)];

    function addCheck(opts) {
        if (opts.every(opt => typeof opt === "number")) { return; }

        const ids = Array.from({ length: N }, (_, i) =>
            opts.map(v => v === "u" ? i : v === "d" ? N - 1 - i : v)).map(vec2id);

        checks.push(ids);
    }

    for (let o1 of options)
        for (let o2 of options)
            for (let o3 of options)
                for (let o4 of options)
                    addCheck([o1, o2, o3, o4]);

    return checks;
}
