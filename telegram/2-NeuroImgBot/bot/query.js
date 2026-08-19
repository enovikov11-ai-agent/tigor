function parseRequest(requestText, hasPhoto, isReply) {
    if (!requestText || (!/(\/r)?@neuroimgbot/i.test(requestText) && !isReply)) {
        return null;
    }

    function getParam(regex, min, def, max) {
        const [, value] = requestText.match(regex) || [0, def];

        return Math.max(Math.min(+value, max), min);
    }

    let count = getParam(/\bcount=(\d+)\b/, 1, 5, 8),
        strength = getParam(/\bstrength=(\d+\.\d+)\b/, 0, 0.2, 1),
        scale = getParam(/\bscale=(\d+(\.\d+)?)\b/, 2, 7.5, 20),
        steps = getParam(/\bsteps=(\d+)\b/, 20, 50, 500),
        request = requestText
            .replace(/(\/r)?@neuroimgbot/i, '')
            .replace(/\b\w+=[\w.]+\b/g, '')
            .replace(/\n/g, ' ')
            .replace(/[ ]+/g, ' ')
            .replace(/^ /, '')
            .replace(/ $/, '');

    if (!request.length) {
        return null;
    }

    count = Math.floor(Math.min(500, count * steps) / steps);

    return {
        count, strength, scale, steps, request,
        origRequest: `${request}\ncount=${count}${hasPhoto ? (' strength=' + strength) : ''} scale=${scale} steps=${steps}`
    };
}

module.exports = { parseRequest };