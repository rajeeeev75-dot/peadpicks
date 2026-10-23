#!/usr/bin/env python3
"""Daily PEAD data fetch: finds NSE stocks that just announced quarterly results,
pulls their last 5 quarters (yfinance) and writes pead.csv for pead-picks.html.
Units written to the CSV: Rs crore for money, Rs for per-share values."""
import csv, os, sys, time, datetime as dt
import requests, pandas as pd, yfinance as yf

RECENT_DAYS = 14        # "just announced" = results filed in the last N days
KEEP_DAYS = 45          # keep older rows in pead.csv this long so picks don't vanish
QTR_MAX_AGE = 120       # ignore stocks whose newest quarter is older than this (days)
CR = 1e7
COLS = ["ticker","name","price","mcap","pe","high52","result_date","quarter_end",
        "rev_cur","rev_prev","rev_yoy","np_cur","np_prev","np_yoy",
        "ebitda_cur","ebitda_prev","ebitda_yoy","eps_cur","eps_prev","eps_yoy",
        "eps_ttm","np_ttm","equity","debt","bvps","earn_ratio","vol_ratio","above_ema200"]

def nse_recent():
    """Best effort: {symbol: result_date} from NSE's financial-results feed. NSE often blocks
    cloud IPs; if so we fall back to tickers.txt and detect new quarters from the data itself."""
    out = {}
    try:
        s = requests.Session()
        h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://www.nseindia.com/"}
        s.get("https://www.nseindia.com", headers=h, timeout=20)
        r = s.get("https://www.nseindia.com/api/corporates-financial-results?index=equities&period=Quarterly",
                  headers=h, timeout=30)
        r.raise_for_status()
        cut = dt.date.today() - dt.timedelta(days=RECENT_DAYS)
        for row in r.json():
            sym = row.get("symbol")
            raw = next((row[k] for k in row if "broadcast" in k.lower() or "filing" in k.lower()), None)
            d = pd.to_datetime(raw, dayfirst=True, errors="coerce")
            if sym and not pd.isna(d) and d.date() >= cut:
                out[sym] = d.date()
    except Exception as e:
        print("NSE feed unavailable:", e, file=sys.stderr)
    return out

def pick(df, names):
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None

def vals(series, n=5):
    return [None if pd.isna(x) else float(x) for x in list(series.values)[:n]] if series is not None else []

def build(sym, rdate):
    t = yf.Ticker(sym + ".NS")
    q = t.quarterly_income_stmt
    if q is None or q.empty or q.shape[1] < 5:
        return None  # need 5 quarters for the YoY comparison
    q = q.sort_index(axis=1, ascending=False)
    qdate = q.columns[0].date()
    if (dt.date.today() - qdate).days > QTR_MAX_AGE:
        return None
    rev = vals(pick(q, ["Total Revenue", "Operating Revenue"]))
    np_ = vals(pick(q, ["Net Income", "Net Income Common Stockholders"]))
    ebd = vals(pick(q, ["EBITDA", "Normalized EBITDA"]))
    eps = vals(pick(q, ["Diluted EPS", "Basic EPS"]))
    if min(len(rev), len(np_), len(ebd), len(eps)) < 5 or None in (rev[0], rev[4], np_[0], np_[4], eps[0]):
        return None
    info = t.info or {}
    bs = t.quarterly_balance_sheet
    eq = debt = None
    if bs is not None and not bs.empty:
        bs = bs.sort_index(axis=1, ascending=False)
        e, d = pick(bs, ["Stockholders Equity", "Common Stock Equity"]), pick(bs, ["Total Debt"])
        eq = None if e is None or pd.isna(e.iloc[0]) else float(e.iloc[0]) / CR
        debt = None if d is None or pd.isna(d.iloc[0]) else float(d.iloc[0]) / CR
    hist = t.history(period="2y", auto_adjust=False)
    earn_ratio = vol_ratio = above = ""
    if len(hist) > 30:
        v, c = hist["Volume"], hist["Close"]
        avg = v.tail(21).iloc[:-1].mean()
        vol_ratio = round(float(v.iloc[-1] / avg), 2) if avg else ""
        if len(c) >= 200:
            above = int(c.iloc[-1] > c.ewm(span=200, adjust=False).mean().iloc[-1])
        if rdate:
            after = hist[hist.index.date > rdate]   # first full session after the announcement
            if len(after):
                i = hist.index.get_loc(after.index[0])
                base = v.iloc[max(0, i - 20):i].mean()
                earn_ratio = round(float(v.iloc[i] / base), 2) if base else ""
    f = lambda x: "" if x is None else round(x / CR, 2)
    r = {"ticker": "NSE:" + sym, "name": info.get("shortName", sym),
         "price": info.get("currentPrice") or info.get("regularMarketPrice") or "",
         "mcap": f(info.get("marketCap")), "pe": info.get("trailingPE") or "", "high52": info.get("fiftyTwoWeekHigh") or "",
         "result_date": rdate.strftime("%d/%m/%Y") if rdate else "", "quarter_end": qdate.isoformat(),
         "rev_cur": f(rev[0]), "rev_prev": f(rev[1]), "rev_yoy": f(rev[4]),
         "np_cur": f(np_[0]), "np_prev": f(np_[1]), "np_yoy": f(np_[4]),
         "ebitda_cur": f(ebd[0]), "ebitda_prev": f(ebd[1]), "ebitda_yoy": f(ebd[4]),
         "eps_cur": eps[0], "eps_prev": eps[1], "eps_yoy": eps[4],
         "eps_ttm": round(sum(x for x in eps[:4] if x is not None), 2),
         "np_ttm": round(sum(x for x in np_[:4] if x is not None) / CR, 2),
         "equity": eq if eq is not None else "", "debt": debt if debt is not None else "",
         "bvps": info.get("bookValue") or "", "earn_ratio": earn_ratio, "vol_ratio": vol_ratio, "above_ema200": above}
    return r

def main():
    recent = nse_recent()
    uni = []
    if os.path.exists("tickers.txt"):
        uni = [x.strip().upper().replace("NSE:", "") for x in open("tickers.txt") if x.strip() and not x.startswith("#")]
    syms = [s for s in recent if not uni or s in uni] if recent else uni
    print(f"Scanning {len(syms)} symbols (NSE feed gave {len(recent)})")
    old = {}
    if os.path.exists("pead.csv"):
        for r in csv.DictReader(open("pead.csv", encoding="utf-8")):
            qd = pd.to_datetime(r.get("quarter_end"), errors="coerce")
            if not pd.isna(qd) and (dt.date.today() - qd.date()).days <= QTR_MAX_AGE and \
               (dt.date.today() - qd.date()).days <= QTR_MAX_AGE:
                old[r["ticker"]] = r
    new = 0
    for s in syms:
        try:
            r = build(s, recent.get(s))
            if r: old[r["ticker"]] = r; new += 1
        except Exception as e:
            print("skip", s, e, file=sys.stderr)
        time.sleep(0.4)
    rows = [r for r in old.values()]
    with open("pead.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} rows ({new} refreshed)")

if __name__ == "__main__":
    main()
