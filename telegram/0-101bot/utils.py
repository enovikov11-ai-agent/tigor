from playwright.async_api import async_playwright
import subprocess
import random
import time
import plotly.express as px
import pandas as pd
from datetime import timedelta
import sqlite3
import math
from IPython.display import display


port = str(random.randint(1024, 65535))
target = "Google Chrome"
fetch_pages = {}
pd.set_option("display.max_rows", None)
global context
global db


def chrome_start():
    subprocess.run(["pkill", target])
    time.sleep(1)
    subprocess.run(["open", "-a", target, "--args",
                   f"--remote-debugging-port={port}"])


async def chrome_connect():
    global context
    playwright = await async_playwright().__aenter__()
    browser = await playwright.chromium.connect_over_cdp(f'http://localhost:{port}/json/version')
    context = browser.contexts[0]


async def fetch(origin, url, params={}, format="json"):
    if origin not in fetch_pages:
        fetch_pages[origin] = await context.new_page()
        await fetch_pages[origin].goto(f"https://{origin}")

    all_params = params | {"mode": "cors", "credentials": "include"}
    return await fetch_pages[origin].evaluate(f'async (url, params) => fetch(url, params).then(res=>res.{format}())', [url, all_params])


def db_connect():
    global db
    db = sqlite3.connect("file:101.sqlite?mode=ro", uri=True)
    db.executescript("""
CREATE TEMPORARY TABLE NumQueries AS SELECT *, ROW_NUMBER() OVER(PARTITION BY number, bot ORDER BY timestamp ASC) AS rn FROM Queries;
CREATE TEMPORARY TABLE FirstQueries AS SELECT * FROM NumQueries WHERE rn = 1 AND number != -1;
                
CREATE TEMPORARY TABLE NumMap AS SELECT user_id, username, ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY timestamp DESC) AS rn FROM Queries;
CREATE TEMPORARY TABLE Map AS SELECT user_id, username FROM NumMap WHERE rn=1;

CREATE TEMPORARY TABLE Owners AS SELECT NFTs.bot, NFTs.number, Map.username FROM NFTs JOIN Map ON NFTs.owner_id = Map.user_id;
CREATE TEMPORARY TABLE Posts AS SELECT * FROM Queries q1 WHERE NOT EXISTS (SELECT 1 FROM Queries q2 WHERE 
    q2.number = q1.number AND q2.user_id = q1.user_id AND q2.bot = q1.bot AND q2.timestamp > q1.timestamp - 7 AND q2.timestamp < q1.timestamp);
    """)


def query(sql, params=()):
    return db.cursor().execute(sql, params).fetchall()


def query_df(sql, params=()):
    c = db.cursor().execute(sql, params)
    return pd.DataFrame(list(c.fetchall()), columns=[column[0] for column in c.description])


def plot_claimrate(log=False):
    df = query_df("""SELECT fq.timestamp - min_fq.min_timestamp as sec, fq.number, fq.bot
FROM FirstQueries fq
JOIN (SELECT bot, MIN(timestamp) as min_timestamp FROM FirstQueries GROUP BY bot) min_fq ON fq.bot = min_fq.bot
ORDER BY fq.timestamp ASC;""")
    if (log):
        df['sec'] = df['sec'].apply(lambda x: math.log(x) if x > 0 else 0)
        tickvals = list([5.5984, 8.5101, 9.9647])
        ticktext = [str(timedelta(seconds=int(math.e ** s))) for s in tickvals]
        return px.line(df, x='sec', y='number', color='bot').update_layout(
            legend=dict(x=0.02, y=0.98), yaxis=dict(title=""), width=700, height=500,
            xaxis=dict(title="", range=[
                       0, 10.2], tickmode="array", tickvals=tickvals, ticktext=ticktext),
        )
    else:
        return px.line(df, x='sec', y='number', color='bot').update_layout(width=700, height=500)


def last101(from_timestamp=time.time()-3600, limit=50):
    queries = query_df(
        f"SELECT datetime(timestamp, 'unixepoch', '+2 hours') as date, timestamp, bot, number, username, id FROM Queries WHERE timestamp > {str(from_timestamp)} ORDER BY timestamp desc LIMIT {str(limit)};")
    results = query_df(
        f"SELECT datetime(timestamp, 'unixepoch', '+2 hours') as date, timestamp, bot, id FROM Results WHERE timestamp > {str(from_timestamp)} ORDER BY timestamp desc LIMIT {str(limit)};")
    queries['timestamp'] = queries['timestamp'].apply(lambda x: str(x))
    results['timestamp'] = results['timestamp'].apply(lambda x: str(x))
    display(queries)
    display(results)
