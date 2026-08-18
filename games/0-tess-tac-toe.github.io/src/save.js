const ENCODE_MAP = map = { "": 0n, "X": 1n, "O": 2n }, DECODE_MAP = ["", "X", "O"],
    BASE62 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

function encodeStateB62(values = getValues()) {
    let encoded = 0n, encText = "";

    for (let i = 0; i < SIZE; i++) {
        encoded = 3n * encoded + ENCODE_MAP[values[i]];
    }

    if (encoded === 0n) { encText = "0"; }

    while (encoded !== 0n) {
        let value = encoded % 62n;
        encoded = (encoded - value) / 62n;
        encText = BASE62[value] + encText;
    }

    return "#" + N + ":" + encText;
}

function decodeStateB62(hash) {
    let text = hash.slice(hash.indexOf(':') + 1), decoded = 0n, values = new Array(SIZE);

    for (let i = 0; i < text.length; i++) {
        let val = BASE62.indexOf(text[i]);
        if (val === -1) { return null; }
        decoded = decoded * 62n + BigInt(val);
    }

    for (let i = SIZE - 1; i >= 0; i--) {
        values[i] = DECODE_MAP[Number(decoded % 3n)];
        decoded /= 3n;
    }

    return values;
}
