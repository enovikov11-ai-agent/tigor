# https://bitinfocharts.com/comparison/monero-mining_profitability.html

profitability = 0.0309 # usd/day / KHash/s
hashrate = 25240.4 / 1000 # KHash/s
night_share = 8 / 24
rsd_usd = 101.12
days = 30

kw = 210 / 1000
price = 3.416
night = 8

monthly_income = days * profitability * hashrate * rsd_usd * night_share
monthly_spend = days * kw * price * night
monthly_profit = monthly_income - monthly_spend

print(f"monthly_profit={monthly_profit:.0f} monthly_income={monthly_income:.0f} monthly_spend={monthly_spend:.0f}")
