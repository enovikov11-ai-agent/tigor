import requests, time, json
import yfinance as yf

yf.Ticker("^XSP").history(period=f"750d").to_csv("./data-v0/XSP.csv")
yf.Ticker("^IRX").history(period=f"750d").to_csv("./data-v0/IRX.csv")

key = "&apiKey=REDACTED"
url = "https://api.polygon.io/v3/reference/options/contracts?underlying_ticker=XSP&contract_type=put&expiration_date.gt=2023-10-25&expiration_date.lt=2025-10-25&expired=true&order=asc&limit=1000&sort=ticker"

results = []

while url:
    if not url.startswith("https://api.polygon.io/"):
        raise Exception("bad url " + url)
    
    res = requests.get(url + key).json()
    print(res)

    results += res["results"]
    url = res["next_url"] if "next_url" in res else None
    time.sleep(12)

with open("./data-v0/XSP-options-2.json", "w") as file:
    json.dump(results, file, indent=2)
