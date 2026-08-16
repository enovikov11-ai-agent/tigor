import random, requests, time, json

with open("./data-v0/XSP-options.json", "r") as file:
    options = {o["ticker"]: o for o in json.load(file)}

with open("./data-v0/XSP-bars.jsonl", "r") as file:
    for line in file:
        item = json.loads(line)
        del options[item["ticker"]]

with open("./data-v0/XSP-bars.jsonl", "a") as file:
    while options:
        ticker = random.choice(list(options.keys()))
        print(ticker, str(len(options) * 12 / 60 / 60) + "h")
        
        try:
            res = requests.get("https://api.polygon.io/v2/aggs/ticker/" + ticker + "/range/1/day/2023-11-01/2025-10-25?adjusted=true&sort=asc&limit=5000&apiKey=REDACTED").json()
            file.write(json.dumps({"ticker": ticker, "res": res}) + "\n")
            file.flush()
        except Exception as e:
            print(e)

        del options[ticker]
        time.sleep(12)
