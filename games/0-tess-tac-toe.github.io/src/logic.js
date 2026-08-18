function play(id, player) {
    if (typeof id !== "number" || id < 0 || id >= SIZE) {
        return console.error("Invalid id ", id);
    }

    const values = getValues(),
        xCount = values.filter(v => v === "X").length,
        oCount = values.filter(v => v === "O").length;

    if (values[id] !== "") {
        return console.error("Already set");
    }

    if (!((player === "X" && xCount === oCount) || (player === "O" && xCount === oCount + 1))) {
        return console.error("Player mismatch");
    }

    setValue(id, player);
}

function getStats(values = getValues()) {
    let xOptions = Array.from({ length: N }, () => ([])),
        oOptions = Array.from({ length: N }, () => ([])),
        stalled = true;

    for (let ids of CHECKS) {
        let counts = { "X": 0, "O": 0, "": 0 }, options = ids.filter(id => values[id] === "");
        ids.forEach(id => counts[values[id]]++);

        if (counts.X === N) { return { winner: "X", highlight: ids }; }
        if (counts.O === N) { return { winner: "O", highlight: ids }; }

        if (counts.X >= 0 && counts.O === 0) { xOptions[counts.X].push(options); stalled = false; }
        if (counts.X === 0 && counts.O >= 0) { oOptions[counts.O].push(options); stalled = false; }
    }

    if (stalled) { return { winner: "stalled", highlight: Array.from({ length: SIZE }, (_, i) => i) }; }
    return { "X": xOptions, "O": oOptions };
}

function aiPlay(player) {
    const opponent = player === "X" ? "O" : "X", values = getValues(), stats = getStats(values);
    if (stats.winner) { return; }

    if (stats[opponent][N - 1].length > 0) {
        return stats[opponent][N - 1][0][0];
    }

    for (let i = N - 1; i > 0; i--) {
        if (stats[player][i].length === 0) { continue; }
        return stats[player][i][0][0];
    }

    return values.map((v, i) => ({ v, i })).find(({ v }) => v === "").i;
}
