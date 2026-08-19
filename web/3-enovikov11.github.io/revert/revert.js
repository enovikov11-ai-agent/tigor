function revertAlgo(str) {
    let arr = str.split(''), i = 0, j = arr.length - 1;
    while (i < j) {
        if (!/[a-z]/i.test(arr[i])) {
            i++;
            continue;
        }

        if (!/[a-z]/i.test(arr[j])) {
            j--;
            continue;
        }

        let buf = arr[i];
        arr[i] = arr[j];
        arr[j] = buf;
        i++;
        j--;
    }

    return arr.join('');
}

if (typeof window !== 'undefined') {
    window.revertAlgo = revertAlgo;
}

if (typeof module !== 'undefined') {
    module.exports = revertAlgo;
}