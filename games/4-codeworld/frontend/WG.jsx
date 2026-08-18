const CHUNK_SIZE = 16, MIN_Y = -64, MAX_Y = 320;
let ctx;

function defaultBoundingBox() {
    return { lx: Infinity, ly: Infinity, lz: Infinity, hx: -Infinity, hy: -Infinity, hz: -Infinity };
}

export const React = {
    createElement(Element = Union, args, ...children) {
        function element() {
            return Element({ ...args, children });
        }

        if (Element.getBoundingBox) {
            element.boundingBox = Element.getBoundingBox({ ...args, children });
        } else {
            let root = Element({ ...args, children });
            while (!root.boundingBox) root = root();
            element.boundingBox = root.boundingBox;
        }

        return element;
    }
};


// https://hub.spigotmc.org/javadocs/bukkit/org/bukkit/Material.html
const MATERIALS = ["AIR", "STONE", "NETHERRACK", "DIRT", "COBBLESTONE",
    "OAK_PLANKS", "TNT", "OBSIDIAN", "GLOWSTONE", "FIRE", "LAVA", "GLASS"];

export function None() { ctx.data[ctx.idx] = 0; }
None.getBoundingBox = defaultBoundingBox;

export function Air() { ctx.data[ctx.idx] = 1; }
Air.getBoundingBox = defaultBoundingBox;

export function Stone() { ctx.data[ctx.idx] = 2; }
Stone.getBoundingBox = defaultBoundingBox;

export function Netherrack() { ctx.data[ctx.idx] = 3; }
Netherrack.getBoundingBox = defaultBoundingBox;

export function Dirt() { ctx.data[ctx.idx] = 4; }
Dirt.getBoundingBox = defaultBoundingBox;

export function Cobblestone() { ctx.data[ctx.idx] = 5; }
Cobblestone.getBoundingBox = defaultBoundingBox;

export function OakPlanks() { ctx.data[ctx.idx] = 6; }
OakPlanks.getBoundingBox = defaultBoundingBox;

export function Tnt() { ctx.data[ctx.idx] = 7; }
Tnt.getBoundingBox = defaultBoundingBox;

export function Obsidian() { ctx.data[ctx.idx] = 8; }
Obsidian.getBoundingBox = defaultBoundingBox;

export function Glowstone() { ctx.data[ctx.idx] = 9; }
Glowstone.getBoundingBox = defaultBoundingBox;

export function Fire() { ctx.data[ctx.idx] = 10; }
Fire.getBoundingBox = defaultBoundingBox;

export function Lava() { ctx.data[ctx.idx] = 11; }
Lava.getBoundingBox = defaultBoundingBox;

export function Glass() { ctx.data[ctx.idx] = 12; }
Glass.getBoundingBox = defaultBoundingBox;


export function Random({ pc, A, B }) {
    return Math.random() < pc ? <A /> : <B />;
}

Random.getBoundingBox = defaultBoundingBox;

export function Mix({ mix }) {
    let random = Math.random();

    for (let key in mix) {
        random -= +key;
        if (random <= 0) {
            mix[key]({});
            return;
        }
    }

    throw new Error("Bad mix");
}

Mix.getBoundingBox = defaultBoundingBox;


export function Union({ children }) {
    for (let i = 0; i < children.length; i++) {
        let tree = children[i];
        while (typeof tree === "function") tree = tree();
    }
}

Union.getBoundingBox = ({ children }) => {
    const boxes = children.map(e => e.boundingBox || e.getBoundingBox());
    return {
        lx: Math.min(...boxes.map(e => e.lx)),
        ly: Math.min(...boxes.map(e => e.ly)),
        lz: Math.min(...boxes.map(e => e.lz)),
        hx: Math.max(...boxes.map(e => e.hx)),
        hy: Math.max(...boxes.map(e => e.hy)),
        hz: Math.max(...boxes.map(e => e.hz))
    };
};


export function Move({ x = 0, y = 0, z = 0, children }) {
    ctx.x -= x;
    ctx.y -= y;
    ctx.z -= z;

    Union({ children });

    ctx.x += x;
    ctx.y += y;
    ctx.z += z;
}

Move.getBoundingBox = ({ x = 0, y = 0, z = 0, children }) => {
    const { lx, ly, lz, hx, hy, hz } = Union.getBoundingBox({ children });
    return { lx: lx + x, ly: ly + y, lz: lz + z, hx: hx + x, hy: hy + y, hz: hz + z };
};


export function Box({ sx, sy, sz, children, hollow = false }) {
    if (ctx.x < 0 || ctx.y < 0 || ctx.z < 0 || ctx.x >= sx || ctx.y >= sy || ctx.z >= sz) return;
    if (hollow && !(ctx.x == 0 || ctx.y == 0 || ctx.z == 0 || ctx.x == sx - 1 || ctx.y == sy - 1 || ctx.z == sz - 1)) {
        Air();
        return;
    }

    Union({ children });
}

Box.getBoundingBox = ({ sx, sy, sz }) => ({ lx: 0, ly: 0, lz: 0, hx: sx - 1, hy: sy - 1, hz: sz - 1 });


export function Extrude({ cx = 1, cy = 1, cz = 1 }) { }
Extrude.getBoundingBox = defaultBoundingBox;
export function Intersection() { }
Intersection.getBoundingBox = defaultBoundingBox;
export function Difference() { }
Difference.getBoundingBox = defaultBoundingBox;
export function Sphere({ x, y, z, r, children, hollow = false }) { }
Sphere.getBoundingBox = defaultBoundingBox;
export function Cylinder({ x, y, z, r, d, children, hollow = false }) { }
Cylinder.getBoundingBox = defaultBoundingBox;
export function AutoLayout({ children }) { }
AutoLayout.getBoundingBox = defaultBoundingBox;
// https://www.thingiverse.com/thing:192392/files
export function Thingiverse({ id, name, size, children }) { }
Thingiverse.getBoundingBox = defaultBoundingBox;


function buildChunks(root, chunks) {
    const height = chunks.map(({ hi, lo }) => hi - lo).reduce((a, b) => a + b);
    ctx = { data: new Uint8Array(CHUNK_SIZE ** 2 * height), idx: 0 };

    for (let i = 0; i < chunks.length; i++) {
        const { x, z, lo, hi } = chunks[i];

        for (let y = lo; y < hi; y++) {
            for (let dx = 0; dx < CHUNK_SIZE; dx++) {
                for (let dz = 0; dz < CHUNK_SIZE; dz++) {
                    ctx.x = CHUNK_SIZE * x + dx;
                    ctx.y = y;
                    ctx.z = CHUNK_SIZE * z + dz;

                    let tree = root;
                    while (typeof tree === "function") tree = tree();

                    ctx.idx++;
                }
            }
        }
    }

    return ctx.data;
}

export async function render(root) {
    const { loaded } = await fetch("http://127.0.0.1:1337/stats").then(res => res.json()),
        { lx, ly, lz, hx, hy, hz } = root.boundingBox,

        chunks = loaded
            .filter(({ x, z }) => Math.floor(lx / CHUNK_SIZE) <= x && x <= Math.floor(hx / CHUNK_SIZE) &&
                Math.floor(lz / CHUNK_SIZE) <= z && z <= Math.floor(hz / CHUNK_SIZE))

            .map(({ x, z }) => ({ x, z, lo: Math.max(MIN_Y, ly), hi: Math.min(MAX_Y, hy + 1) })),

        meta = { materials: MATERIALS, chunks },
        body = buildChunks(root, chunks);

    await fetch("http://127.0.0.1:1337/chunks", {
        method: "POST", body,
        headers: { "Content-Type": "application/octet-stream", "X-Meta": JSON.stringify(meta) }
    }).then(res => res.text()).then(console.log);
}
