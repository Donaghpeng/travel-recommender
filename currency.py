"""
currency.py — 汇率查询工具
尝试在线获取汇率，离线时使用缓存数据
"""
import urllib.request, json, os, time

API_URL = "https://api.exchangerate-api.com/v4/latest/CNY"
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".currency_cache.json")

# 离线备用汇率 (2026-06 基准)
FALLBACK = {
    "USD": 0.137, "EUR": 0.127, "GBP": 0.108, "JPY": 21.50,
    "KRW": 186.0, "THB": 4.99, "MYR": 0.648, "SGD": 0.185,
    "HKD": 1.070, "AUD": 0.210, "VND": 3485, "IDR": 2120
}
SYMBOLS = {"USD":"$","EUR":"E","GBP":"P","JPY":"Y","KRW":"W",
           "THB":"B","MYR":"RM","SGD":"S$","HKD":"HK$","AUD":"A$","VND":"d","IDR":"Rp"}

def get_rates():
    data = None
    try:
        resp = urllib.request.urlopen(API_URL, timeout=4)
        data = json.loads(resp.read().decode()).get("rates", {})
        with open(CACHE_FILE, "w") as f:
            json.dump({"time": time.time(), "rates": data}, f)
        print("  [在线] 汇率已更新")
    except:
        if os.path.exists(CACHE_FILE):
            try:
                cache = json.load(open(CACHE_FILE))
                if time.time() - cache["time"] < 86400:
                    data = cache["rates"]
                    print("  [缓存] 24小时内缓存")
            except (json.JSONDecodeError, FileNotFoundError, KeyError):
                pass
    if not data:
        data = FALLBACK
        print("  [离线] 使用备用汇率")
    return data

def convert(amount, frm, to, rates):
    if frm == "CNY" and to in rates:
        return amount * rates[to]
    if frm in rates and to == "CNY":
        return amount / rates[frm]
    if frm in rates and to in rates:
        return (amount / rates[frm]) * rates[to]
    return None

def main():
    rates = get_rates()
    targets = ["USD","EUR","JPY","THB","KRW","MYR","SGD","VND","AUD","GBP"]

    print()
    print("  [货币] 实时汇率看板 (基准: CNY)")
    print("  " + "-" * 30)
    for code in targets:
        if code in rates:
            print(f"  {code:6s} {SYMBOLS.get(code,'?'):4s} 1 CNY = {rates[code]:10.4f} {code}")

    budget = 4000
    print()
    print("  [预算] 4000元换算:")
    for code, name in [("USD","USD"),("THB","THB"),("JPY","JPY")]:
        r = convert(budget, "CNY", code, rates)
        if r:
            print(f"    -> {name}: {r:>10,.0f}")

if __name__ == "__main__":
    main()
