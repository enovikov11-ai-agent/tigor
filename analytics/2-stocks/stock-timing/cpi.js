// https://data.bls.gov/timeseries/CUUR0000SA0?years_option=all_years

cpi = {};

for (let lineEl of document.querySelector("#table0 tbody").querySelectorAll("tr")) {
    const line = lineEl.querySelectorAll("td");

    for (let month = 1; month <= 12; month++) {
        if (line[month].innerText !== "") {
            cpi[line[0].innerText + "-" + (month + "").padStart(2, "0")] = +line[month].innerText;
        }
    }
}

document.body.innerText = JSON.stringify(cpi);
