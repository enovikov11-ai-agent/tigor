const nonEsg = {
    "fastfood": ["KO", "PEP", "SJM", "YUMC", "CAKE", "QSR", "MCD", "JACK", "LOCO", "BLMN", "WEN", "DPZ", "TXRH", "WING", "BJRI", "SG", "CAG", "YUM", "DRI", "CMG", "HSY", "PZZA", "SBUX", "DENN"],
    "tobacco": ["TPB", "RLX", "UVV", "PM", "MO", "BTI"],
    "alcohol": ["AB", "ABEV", "STZ", "CCU", "BUD", "FMX", "SAM", "DEO", "TAP"],
    "gambling": ["GLPI", "SGHC", "RSI", "LVS", "MGM", "PENN", "CHDN", "EVRI", "BYD", "AGS", "WYNN", "VICI", "BALY", "CZR", "DKNG"],
    "weed": ["OGI", "IIPR", "SNDL", "TLRY", "VFF", "GRWG", "ACB", "CGC", "HYFM"],
    "hft": ["CME", "NDAQ", "ICE", "MKTX", "IBKR", "VIRT", "SCHW", "TTD", "HOOD", "CBOE"],
    "luxury": ["RL", "KSS", "SKX", "MOV", "PVH", "CPRI", "SIG", "ANF", "EL", "GES", "FOSL", "TPR", "BIRK"]
};

const tickers = new Set(Object.values(nonEsg).reduce((a, b) => a.concat(b)));
const stockData = [];

for (let ticker of tickers) {
    const res = await fetch("https://query2.finance.yahoo.com/v8/finance/chart/" + ticker);
    const json = await res.json();
    const result = json.chart.result;

    if (!result) { continue; }

    const meta = result[0].meta;
    const data = [meta.symbol, meta.regularMarketPrice * meta.regularMarketVolume, meta.currency, meta.fullExchangeName, meta.longName];
    stockData.push(data)
}

document.body.innerText = JSON.stringify(stockData);
