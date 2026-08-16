import requests, json

key = "&apiKey=***REMOVED***"
url = "https://api.polygon.io/v3/reference/options/contracts?expired=true&order=asc&limit=1000&sort=ticker"

with open("./data-v1/contracts.jsonl", "a") as file:
    while url:
        if not url.startswith("https://api.polygon.io/"):
            raise Exception("bad url " + url)
        
        res = requests.get(url + key).json()

        file.write(json.dumps(res["results"]) + "\n")
        file.flush()
        
        url = res["next_url"] if "next_url" in res else None