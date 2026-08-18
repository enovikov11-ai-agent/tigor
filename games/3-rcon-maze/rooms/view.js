addEventListener('load', async () => {

const pixelSize = 20, maze = mazeGenerator(), canvas = document.createElement("canvas"),
    ctx = canvas.getContext("2d");
document.body.appendChild(canvas);

for(let {x, y, hasBlock, type} of maze) {
    switch(type){
        case 'setSize':
            canvas.width = pixelSize * x;
            canvas.height = pixelSize * y;
            break;
        case 'setBlock':
            ctx.beginPath();
            ctx.rect(pixelSize * x, pixelSize * y, pixelSize, pixelSize);
            ctx.fillStyle = hasBlock ? "#000000" : "#ffffff";
            ctx.fill();
            break;
    }
}

});