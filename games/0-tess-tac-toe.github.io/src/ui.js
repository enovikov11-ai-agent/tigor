function swap(key) {
    const states = SWAPS[key].map(id => ({ text: cells[id].innerText, color: cells[id].style.background }));

    for (let i = 0; i < SIZE; i++) {
        cells[i].innerText = states[i].text;
        cells[i].style.background = states[i].color;
    }
}

function makeTable({ item = () => "", name = "main", prefix = "m" }) {
    const createRow = (_, rowIndex) => {
        const createCell = (_, colIndex) =>
            `<td class="${name}" id="${prefix}_${rowIndex}_${colIndex}">${item(rowIndex, colIndex)}</td>`;

        return `<tr>${Array.from({ length: N }, createCell).join("")}</tr>`;
    };

    const body = Array.from({ length: N }, createRow).join("");
    return `<table class="${name}"><tbody>${body}</tbody></table>`;
}

function render() {
    const buttons = Object.keys(SWAPS).map(key => `<button onclick="swap('${key}')">Swap ${key}</button>`).join(""),
        table = makeTable({ item: (x, y) => makeTable({ name: "inner", prefix: `i_${x}_${y}` }) });

    document.body.innerHTML = `<center><div>${buttons}</div>${table}</center>`;

    let cells = new Array(N ** 4);
    forEachVec(([x, y, z, w]) => cells[vec2id([x, y, z, w])] = document.getElementById(`i_${x}_${y}_${z}_${w}`));
    return cells;
}

function getValues() {
    return cells.map(cell => cell.innerText);
}

function setValue(id, player) {
    cells[id].innerText = player;
}

function checkWinner() {
    const stats = getStats(getValues());

    if (stats.winner) {
        stats.highlight.forEach(id => cells[id].style.background = "lightgray");
        document.removeEventListener("click", onClick);
        return true;
    } else {
        return false;
    }
}

function onClick({ target }) {
    const id = cells.indexOf(target);
    if (id === -1) { return; }

    play(id, "X");
    if (checkWinner()) { return; }
    play(aiPlay("O"), "O");
    checkWinner();
}

function getRootSize() {
    if (N <= 3) { return 8.5; }
    if (N === 4) { return 4.1; }
    if (N === 5) { return 2.3; }
    return 1.5;
}

const cells = render();
document.addEventListener("click", onClick);

navigator?.serviceWorker?.register('/sw.js');
document.getElementById("vars").innerText = `:root { --size: ${getRootSize()}vmin; }`;