function clusterPlot(rawPoints, { gridSize = 8 } = {}) {
    const ITERATIONS_COUNT = 3, SCALE_FACTOR = 4;

    function unionRaw(rawPoints) {
        const sumCount = rawPoints.length;

        return {
            x: rawPoints.map(([x]) => x).reduce((a, b) => a + b, 0) / sumCount,
            y: rawPoints.map(([, y]) => y).reduce((a, b) => a + b, 0) / sumCount,
            count: sumCount
        }
    }

    function union(points) {
        const sumCount = points.map(({ count }) => count).reduce((a, b) => a + b, 0);

        return {
            x: points.map(({ x, count }) => x * count).reduce((a, b) => a + b, 0) / sumCount,
            y: points.map(({ y, count }) => y * count).reduce((a, b) => a + b, 0) / sumCount,
            count: sumCount
        };
    }

    function grid(rawPoints, size) {
        const clusters = {};

        for (let [x, y] of rawPoints) {
            const id = Math.floor(x * size * (1 - 1e-10)) + Math.floor(y * size * (1 - 1e-10)) * size;
            clusters[id] = clusters[id] || [];
            clusters[id].push([x, y]);
        }

        return Object.values(clusters).map(unionRaw);
    }

    function kMeans(points, basePoints) {
        const clusters = {};

        for (let i = 0; i < points.length; i++) {
            const id = basePoints.map((point, id) => ({
                diff: (points[i].x - point.x) ** 2 + (points[i].y - point.y) ** 2,
                id
            })).reduce((a, b) => a.diff < b.diff ? a : b).id;

            clusters[id] = clusters[id] || [];
            clusters[id].push(points[i])
        }

        return Object.values(clusters).map(union);
    }

    function overlap(points) {
        const mapper = new Array(points.length).fill().map((_, i) => i);
        const clusters = {};

        for (let i = 0; i < points.length; i++) {
            for (let j = i + 1; j < points.length; j++) {
                const a = points[i], b = points[j],
                    rSum = (Math.sqrt(a.count / rawPoints.length) + Math.sqrt(b.count / rawPoints.length)) / gridSize,
                    d = Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);

                if (rSum / d > 0.9) {
                    mapper[j] = mapper[i];
                }
            }
        }

        mapper.forEach((id, i) => {
            clusters[id] = clusters[id] || [];
            clusters[id].push(points[i]);
        });

        return Object.values(clusters).map(union);
    }

    let points = grid(rawPoints, gridSize * SCALE_FACTOR), basePoints = grid(rawPoints, gridSize);

    for (let i = 0; i < ITERATIONS_COUNT; i++) {
        basePoints = overlap(kMeans(points, basePoints))
    }

    return basePoints.map(({ x, y, count }) => ({ x, y, count, r: Math.sqrt(count / rawPoints.length) / gridSize }));
}

if (typeof window !== "undefined") {
    window.clusterPlot = clusterPlot;
}

if (typeof module !== "undefined") {
    module.exports = clusterPlot;
}
