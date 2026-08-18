const { isPoint, isArea, sum, isSubarea, moveArea, isFloatArea, refitArea } = require("./lib/math");
const { fill, close } = require("./lib/native");
const world = require("./world");

function applyContext(parent, children) {
    const appliedChildren = [];

    for (let { relativePoint, relativeArea, ...childArgs } of children) {

        // Guess absolutePoint
        if (!isPoint(childArgs.absolutePoint) && isPoint(parent.absolutePoint)) {
            relativePoint = isPoint(relativePoint) ? relativePoint : [0, 0, 0];
            childArgs.absolutePoint = sum(parent.absolutePoint, relativePoint);
        }

        // Guess absoluteArea
        if (!isArea(childArgs.absoluteArea) && isArea(relativeArea) &&
            isPoint(childArgs.absolutePoint)) {

            childArgs.absoluteArea = moveArea(relativeArea, childArgs.absolutePoint);
        }

        // Guess absoluteArea
        if (!isArea(childArgs.absoluteArea) && isArea(parent.absoluteArea)) {
            childArgs.absoluteArea = parent.absoluteArea;
        }

        // Guess material
        childArgs.material = childArgs.material || parent.material;

        // Refit area
        if (isFloatArea(childArgs.areaScaler) && isArea(childArgs.absoluteArea)) {
            childArgs.absoluteArea = refitArea(childArgs.absoluteArea, childArgs.areaScaler);
        }

        // Push only if ok
        if (isArea(childArgs.absoluteArea) && (!isArea(parent.absoluteArea) ||
            isSubarea(childArgs.absoluteArea, parent.absoluteArea))) {
            appliedChildren.push(childArgs);
        }
    }

    return appliedChildren;
}

async function execute({ run, ...args }) {
    if (!/^(@[a-z0-9][a-z0-9_-]{0,50}\/)?[a-z0-9][a-z0-9_-]{0,50}$/i.test(run)) {
        return;
    }

    if (run === "fill") {
        await fill(args);
        return;
    }

    if (!world[run]) {
        return;
    }

    const children = [...world[run](args)];
    const appliedChildren = applyContext(args, children);
    for (let child of appliedChildren) {
        await execute(child);
    }
}

execute({ run: "world" }).catch(console.error).then(close);