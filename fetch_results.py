#!/usr/bin/env python3
"""Daily PEAD data fetch: finds NSE stocks that just announced quarterly results,
pulls their last quarters (yfinance) and writes pead.csv for peadpicks.html.
Units written to the CSV: Rs crore for money, Rs for per-share values.

Changes vs the previous version
- Never skips silently: every rejected stock logs the reason (see the Action log).
- Uses the newest quarter that actually has revenue + net income. Yahoo often adds the new
  quarter as a half-empty column first; the old code rejected the stock and kept the old row.
- Year-ago quarter is found by date, not by "column number 4".
- EBITDA falls back to EBIT + depreciation; EPS falls back to net income / shares.
- TTM EPS / profit are written only when all 4 quarters exist (no under-counted sums).
- Retries Yahoo calls (GitHub runners get rate-limited now and then).
- Old rows that could not be refreshed are kept but tagged in the feed_note column.
- Optional overrides.csv: type a newer quarter by hand while the feed lags.
"""
import csv, os, sys, time, datetime as dt
import requests, pandas as pd, yfinance as yf

RECENT_DAYS = 14        # "just announced" = results filed in the last N days
KEEP_DAYS = 45          # (kept for reference)
QTR_MAX_AGE = 120       # ignore stocks whose newest quarter is older than this (days)
CR = 1e7
COLS = ["ticker","name","price","mcap","pe","high52","result_date","quarter_end",
        "rev_cur","rev_prev","rev_yoy","np_cur","np_prev","np_yoy",
        "ebitda_cur","ebitda_prev","ebitda_yoy","eps_cur","eps_prev","eps_yoy",
        "eps_ttm","np_ttm","equity","debt","bvps","earn_ratio","vol_ratio","above_ema200",
        "feed_note"]


class Skip(Exception):
    """Raised with a human-readable reason when a stock cannot be (re)built."""


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


def last_quarter_end(today):
    ends = [dt.date(y, m, d) for y in (today.year - 1, today.year) for m, d in ((3, 31), (6, 30), (9, 30), (12, 31))]
    return max(e for e in ends if e < today)


def pick(df, names):
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None


def at(series, i):
    """float at position i, or None if the row/column/value is missing."""
    if series is None or i is None or i >= len(series):
        return None
    x = series.iloc[i]
    return None if pd.isna(x) else float(x)


def get_quarters(t):
    for attempt in range(3):
        try:
            q = t.quarterly_income_stmt
            if q is None or q.empty:
                q = t.quarterly_financials
            if q is not None and not q.empty:
                return q.sort_index(axis=1, ascending=False)
        except Exception as e:
            print("  yahoo error:", e, file=sys.stderr)
        time.sleep(2 * (attempt + 1))
    return None


def build(sym, rdate):
    t = yf.Ticker(sym + ".NS")
    q = get_quarters(t)
    if q is None:
        raise Skip("Yahoo returned no quarterly statements")
    rev_s0, np_s0 = pick(q, ["Total Revenue", "Operating Revenue"]), pick(q, ["Net Income", "Net Income Common Stockholders"])
    if rev_s0 is None or np_s0 is None:
        raise Skip("revenue / net income rows missing in Yahoo data")
    cols = list(q.columns)
    use = next((i for i in range(len(cols)) if not pd.isna(rev_s0.iloc[i]) and not pd.isna(np_s0.iloc[i])), None)
    if use is None:
        raise Skip("no quarter with both revenue and net income")
    notes = []
    if use > 0:
        notes.append("Yahoo has newer incomplete quarter(s) " + ",".join(c.date().isoformat() for c in cols[:use]))
    q = q.iloc[:, use:]
    cols = list(q.columns)
    qdate = cols[0].date()
    if (dt.date.today() - qdate).days > QTR_MAX_AGE:
        raise Skip(f"newest usable quarter {qdate} is older than {QTR_MAX_AGE} days")
    gap = lambda i: (qdate - cols[i].date()).days
    if len(cols) < 2 or not 60 <= gap(1) <= 125:
        raise Skip("previous quarter missing in Yahoo data")
    j = next((i for i in range(1, len(cols)) if abs(gap(i) - 365) <= 20), None)
    if j is None:
        raise Skip(f"year-ago quarter missing (Yahoo gave {len(cols)} quarters)")

    rev_s, np_s = pick(q, ["Total Revenue", "Operating Revenue"]), pick(q, ["Net Income", "Net Income Common Stockholders"])
    ebd_s = pick(q, ["EBITDA", "Normalized EBITDA"])
    ebit_s = pick(q, ["EBIT", "Operating Income"])
    da_s = pick(q, ["Reconciled Depreciation", "Depreciation And Amortization In Income Statement",
                    "Depreciation Amortization Depletion Income Statement"])
    eps_s = pick(q, ["Diluted EPS", "Basic EPS"])

    def ebitda_at(i):
        e = at(ebd_s, i)
        if e is None:
            a, b = at(ebit_s, i), at(da_s, i)
            if a is not None and b is not None:
                e = a + b
        return e

    rev = [at(rev_s, i) for i in (0, 1, j)]
    np_ = [at(np_s, i) for i in (0, 1, j)]
    ebd = [ebitda_at(i) for i in (0, 1, j)]
    eps = [at(eps_s, i) for i in (0, 1, j)]
    if None in (rev[0], rev[1], rev[2], np_[0], np_[1], np_[2]):
        raise Skip("revenue/net income missing for current, previous or year-ago quarter")

    try:
        info = t.info or {}
    except Exception as e:
        print("  yahoo info error:", e, file=sys.stderr)
        info = {}
    if not info:
        raise Skip("Yahoo info (price, market cap) unavailable, possibly rate limited")
    if eps[0] is None:
        sh = info.get("sharesOutstanding")
        if sh:
            eps[0] = np_[0] / sh
            notes.append("EPS derived from net income / shares")
        else:
            raise Skip("EPS missing and shares outstanding unknown")
    if ebd[0] is None or ebd[2] is None:
        notes.append("EBITDA missing (margin change will read as 0)")

    four = lambda s: [at(s, i) for i in range(4)] if len(cols) >= 4 else [None]
    eps4, np4 = four(eps_s), four(np_s)
    eps_ttm = round(sum(eps4), 2) if None not in eps4 and len(eps4) == 4 else ""
    np_ttm = round(sum(np4) / CR, 2) if None not in np4 and len(np4) == 4 else ""

    bs = t.quarterly_balance_sheet
    eq = debt = None
    if bs is not None and not bs.empty:
        bs = bs.sort_index(axis=1, ascending=False)
        e, d = pick(bs, ["Stockholders Equity", "Common Stock Equity"]), pick(bs, ["Total Debt"])
        eq = None if e is None or pd.isna(e.iloc[0]) else float(e.iloc[0]) / CR
        debt = None if d is None or pd.isna(d.iloc[0]) else float(d.iloc[0]) / CR
    try:
        hist = t.history(period="2y", auto_adjust=False)
    except Exception:
        hist = pd.DataFrame()
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
    return {"ticker": "NSE:" + sym, "name": info.get("shortName", sym),
            "price": info.get("currentPrice") or info.get("regularMarketPrice") or "",
            "mcap": f(info.get("marketCap")), "pe": info.get("trailingPE") or "", "high52": info.get("fiftyTwoWeekHigh") or "",
            "result_date": rdate.strftime("%d/%m/%Y") if rdate else "", "quarter_end": qdate.isoformat(),
            "rev_cur": f(rev[0]), "rev_prev": f(rev[1]), "rev_yoy": f(rev[2]),
            "np_cur": f(np_[0]), "np_prev": f(np_[1]), "np_yoy": f(np_[2]),
            "ebitda_cur": f(ebd[0]), "ebitda_prev": f(ebd[1]), "ebitda_yoy": f(ebd[2]),
            "eps_cur": eps[0], "eps_prev": eps[1], "eps_yoy": eps[2],
            "eps_ttm": eps_ttm, "np_ttm": np_ttm,
            "equity": eq if eq is not None else "", "debt": debt if debt is not None else "",
            "bvps": info.get("bookValue") or "", "earn_ratio": earn_ratio, "vol_ratio": vol_ratio,
            "above_ema200": above, "feed_note": "; ".join(notes)}


def apply_overrides(rows):
    """overrides.csv (optional): same columns as pead.csv. Only ticker, quarter_end and the result
    columns are needed; blank cells keep the fetched value. Used only while the feed is behind."""
    if not os.path.exists("overrides.csv"):
        return
    for r in csv.DictReader(open("overrides.csv", encoding="utf-8")):
        tk = (r.get("ticker") or "").strip().upper()
        qd = (r.get("quarter_end") or "").strip()
        if not tk or not qd:
            continue
        if not tk.startswith("NSE:"):
            tk = "NSE:" + tk
        cur = rows.get(tk)
        if cur and (cur.get("quarter_end") or "") >= qd:
            print(f"OVERRIDE not needed for {tk}: feed already has {cur.get('quarter_end')}")
            continue
        base = dict(cur or {})
        for k in ("eps_prev", "eps_yoy", "eps_ttm", "np_ttm", "result_date", "earn_ratio"):
            base[k] = ""   # old-quarter values would be wrong; the page derives TTM EPS from P/E when blank
        base.update({k: v for k, v in r.items() if k in COLS and v not in (None, "")})
        base["ticker"], base["quarter_end"], base["feed_note"] = tk, qd, "manual override"
        rows[tk] = base
        print(f"OVERRIDE applied for {tk}: quarter {qd}")


def main():
    today = dt.date.today()
    expected = last_quarter_end(today)
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
            if not pd.isna(qd) and (today - qd.date()).days <= QTR_MAX_AGE:
                old[r["ticker"]] = r
    new, behind, skipped = 0, [], []
    for s in syms:
        key = "NSE:" + s
        try:
            r = build(s, recent.get(s))
            if dt.date.fromisoformat(r["quarter_end"]) < expected:
                note = f"newest quarter {r['quarter_end']} is behind calendar quarter {expected}"
                r["feed_note"] = "; ".join(x for x in (r["feed_note"], note) if x)
                behind.append(f"{s} ({r['quarter_end']})")
            old[key] = r
            new += 1
            print(f"OK    {s}: quarter {r['quarter_end']}" + (f"  [{r['feed_note']}]" if r["feed_note"] else ""))
        except Skip as e:
            print(f"SKIP  {s}: {e}")
            skipped.append(s)
            if key in old:
                old[key]["feed_note"] = f"stale, not refreshed: {e}"
        except Exception as e:
            print(f"ERROR {s}: {type(e).__name__}: {e}", file=sys.stderr)
            skipped.append(s)
            if key in old:
                old[key]["feed_note"] = f"stale, not refreshed: {type(e).__name__}"
        time.sleep(0.4)
    apply_overrides(old)
    rows = list(old.values())
    with open("pead.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} rows ({new} refreshed, {len(skipped)} skipped, {len(behind)} behind calendar quarter {expected})")
    if behind:
        print("BEHIND (feed newest quarter older than last calendar quarter):", ", ".join(behind[:40]))
    if skipped:
        print("SKIPPED:", ", ".join(skipped[:40]))


if __name__ == "__main__":
    main()
