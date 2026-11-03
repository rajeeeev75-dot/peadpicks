#!/usr/bin/env python3
"""
PEAD back-test: how did "excellent results + high volume + positive reaction" do after the result, in the past?

For every stock it rebuilds each past quarter's result from Screener.in (about 3 years of quarters), scores it with the SAME
rules as the PEAD Picks tab, finds the real announcement date (NSE filing date; if NSE refuses, the day of the volume spike),
measures the market reaction and the volume surge, and then follows the stock for 5, 20 and 60 trading days from the close of
the first session after the result (the moment the reaction is known), against the Nifty over the same days.

Output files (written next to pead.csv): pead_backtest.json (the page reads this), pead_backtest.csv (every event, so you can audit it),
pead_backtest.md (the same tables as text) and backtest_cache.json (resume file: a run picks up where the last one stopped).

Usage:   python pead_backtest.py            (normal run, stops after BUDGET_MIN minutes, resumes next time)
         python pead_backtest.py --aggregate (only rebuild the tables from the cache)
Env:     BT_MAX (stocks per run, default 400)  BUDGET_MIN (minutes, default 100)  BT_REFRESH=1 (ignore the cache)
"""
import csv, json, math, os, random, re, statistics as st, sys, time, datetime as dt
import requests, pandas as pd, yfinance as yf
from fetch_results import parse_screener, SCR_HEAD, filing_date

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "backtest_cache.json")
OUT_JSON, OUT_CSV, OUT_MD = (os.path.join(HERE, n) for n in ("pead_backtest.json", "pead_backtest.csv", "pead_backtest.md"))
HORIZONS = (5, 20, 60)
BUDGET_MIN = float(os.environ.get("BUDGET_MIN", "100"))
BT_MAX = int(os.environ.get("BT_MAX", "400"))


# ------------------------------------------------------------------ score: a line-by-line port of score() in the PEAD Picks tab ("auto" forward P/E mode)
def _ok(v):
    return v is not None and not (isinstance(v, float) and math.isnan(v))


def nz(v):
    return v if _ok(v) else 0.0


def clamp(v, lo, hi):
    return min(max(v, lo), hi)


def pgrow(cur, base):
    b = nz(base)
    return (nz(cur) - b) / abs(b) * 100 if b != 0 else 0.0


def p_yoy(g): return 6 if g >= 40 else 6 * (g - 15) / 25 if g >= 15 else 2 * g / 15 if g >= 0 else 0
def p_qoq(g): return 4 if g >= 20 else 4 * (g - 5) / 15 if g >= 5 else 1.5 * g / 5 if g >= 0 else 0
def p_edy(g): return 6 if g >= 1 else 6 * (g - 0.3) / 0.7 if g >= 0.3 else 2 * g / 0.3 if g >= 0 else 0
def p_edq(g): return 4 if g >= 0.5 else 4 * (g - 0.2) / 0.3 if g >= 0.2 else 1.5 * g / 0.2 if g >= 0 else 0


def p_gpe(r):
    if not _ok(r): return 0
    return 10 if r >= 2.5 else 8 if r >= 1.8 else 6 if r >= 1.2 else 5 if r >= 0.75 else 3 if r >= 0.5 else 1 if r >= 0.25 else 0 if r >= 0 else -3


def p_sur(a): return 10 if a >= 50 else 10 * (a - 20) / 30 if a >= 20 else 3 * a / 20 if a >= 0 else 0
def p_vol(r): return 0 if not _ok(r) else 5 if r >= 2 else 3 if r >= 1.5 else 0 if r >= 1 else -5


def score(rev, np_, ebd, eps0, eps_ttm, price, pe, er, vr=None):
    """rev, np_, ebd = [current quarter, previous quarter, same quarter a year ago]. Returns (total, label)."""
    if not _ok(rev[0]) or not _ok(np_[0]):
        return None
    mar = lambda i: nz(ebd[i]) / nz(rev[i]) * 100 if nz(rev[i]) != 0 else 0.0
    rev_q, rev_y, np_q, np_y = pgrow(rev[0], rev[1]), pgrow(rev[0], rev[2]), pgrow(np_[0], np_[1]), pgrow(np_[0], np_[2])
    eb_q, eb_y = mar(0) - mar(1), mar(0) - mar(2)
    avg_yoy = (rev_y + np_y + eb_y) / 3
    capped = clamp(avg_yoy, 0, 60)
    ttm = eps_ttm if _ok(eps_ttm) and eps_ttm != 0 else ((price / pe) if _ok(price) and _ok(pe) and pe > 0 else 0)
    runrate = eps0 * 4 if nz(eps0) > 0 else 0
    pead_e = ttm * (1 + capped / 100) if ttm > 0 else 0
    fwd = max(runrate, pead_e)
    fwd_pe = price / fwd if fwd > 0 and _ok(price) else 0
    s_sales = p_yoy(rev_y) * (13 / 6) + p_qoq(rev_q) * (7 / 4)
    s_np = p_yoy(np_y) * (10 / 6) + p_qoq(np_q) * (5 / 4)
    s_eb = p_edy(eb_y) * (7 / 6) + p_edq(eb_q) * (3 / 4)
    gpe = capped / fwd_pe if fwd_pe > 0 else float("nan")
    s_gpe = p_gpe(gpe) * 2
    avg_q = (rev_q + np_q + eb_q) / 3
    accel = avg_yoy - abs(avg_q) * 4
    s_sur = p_sur(accel) * 2.5
    pos = sum(1 for x in (rev_y, rev_q, np_y, np_q, eb_y, eb_q) if x > 0)
    bonus = 10 if pos / 6 >= 0.75 else 0
    vol_adj = p_vol(min(er, vr if _ok(vr) else er)) if _ok(er) else 0
    total = clamp(s_sales + s_np + s_eb + s_gpe + s_sur + bonus + vol_adj, 0, 100)
    label = "EXCELLENT" if total >= 80 else "VERY GOOD" if total >= 65 else "GOOD" if total >= 45 else "WEAK" if total >= 30 else "POOR"
    return total, label


# ------------------------------------------------------------------ data
def d2(s):
    return dt.date.fromisoformat(str(s)[:10])


def get_screener(sym):
    for path in ("/consolidated/", "/"):
        time.sleep(1.2)
        try:
            r = requests.get(f"https://www.screener.in/company/{sym}{path}", headers=SCR_HEAD, timeout=30)
        except Exception:
            return None, "unreachable"
        if r.status_code in (429, 403):
            time.sleep(15)
            return None, f"http{r.status_code}"
        if r.status_code != 200:
            continue
        P = parse_screener(r.text)
        if P:
            return P, ""
    return None, "no table"


NSE = {"s": None, "h": None, "fail": 0, "off": False}


def nse_start():
    try:
        s = requests.Session()
        h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-financial-results"}
        s.get("https://www.nseindia.com", headers=h, timeout=20)
        s.get("https://www.nseindia.com/companies-listing/corporate-filings-financial-results", headers=h, timeout=20)
        NSE["s"], NSE["h"] = s, h
    except Exception as e:
        NSE["off"] = True
        print("NSE not reachable, using volume-spike dates:", e, file=sys.stderr)


def nse_dates(sym):
    """{quarter end 'YYYY-MM-DD': first filing date} for one stock, from NSE's results history."""
    if NSE["off"] or NSE["s"] is None:
        return {}
    try:
        r = NSE["s"].get("https://www.nseindia.com/api/corporates-financial-results?index=equities&symbol=" + requests.utils.quote(sym) + "&period=Quarterly", headers=NSE["h"], timeout=25)
        r.raise_for_status()
        rows = r.json()
        rows = rows if isinstance(rows, list) else rows.get("data", [])
    except Exception:
        NSE["fail"] += 1
        if NSE["fail"] >= 8:
            NSE["off"] = True
            print("NSE refused 8 requests, using volume-spike dates for the rest of this run", file=sys.stderr)
        return {}
    NSE["fail"] = 0
    out = {}
    for row in rows:
        q = pd.to_datetime(row.get("toDate"), dayfirst=True, errors="coerce")
        d = filing_date(row)
        if d is not None and not pd.isna(q):
            k = q.date().isoformat()
            if k not in out or d < out[k]:
                out[k] = d
    time.sleep(0.4)
    return out


def get_hist(sym):
    try:
        h = yf.Ticker(sym + ".NS").history(period="6y", auto_adjust=False)
        if h is None or len(h) < 100:
            return None
        return [(d.date(), float(o), float(c), float(v)) for d, o, c, v in zip(h.index, h["Open"], h["Close"], h["Volume"])]
    except Exception:
        return None


def get_nifty():
    h = yf.Ticker("^NSEI").history(period="6y", auto_adjust=False)
    return {d.date(): float(c) for d, c in zip(h.index, h["Close"])}


# ------------------------------------------------------------------ one stock -> events
def spike_date(rows, qend):
    """Fallback announcement date: the day of the biggest volume spike 10-80 days after the quarter end (reaction day = that day)."""
    lo, hi = qend + dt.timedelta(days=10), qend + dt.timedelta(days=80)
    best, bi = 0, None
    for i in range(21, len(rows)):
        if not (lo <= rows[i][0] <= hi):
            continue
        base = sum(r[3] for r in rows[i - 20:i]) / 20
        ratio = rows[i][3] / base if base else 0
        if ratio > best:
            best, bi = ratio, i
    return rows[bi - 1][0] if bi else None


def stock_events(sym, P, rows, nifty, ann):
    q, ds = P["q"], P["dates"]
    g = lambda lab, d: (q.get(lab) or {}).get(d)
    n = len(rows)
    dts = [r[0] for r in rows]
    n_dates = sorted(nifty)
    out = []

    def nifty_at(d):
        lo, hi = 0, len(n_dates) - 1
        r = None
        while lo <= hi:
            m = (lo + hi) // 2
            if n_dates[m] <= d: r, lo = n_dates[m], m + 1
            else: hi = m - 1
        return nifty.get(r) if r else None

    for k, cur in enumerate(ds):
        cd = d2(cur)
        gap = lambda d: (cd - d2(d)).days
        prev = next((d for d in reversed(ds[:k]) if 60 <= gap(d) <= 125), None)
        yago = next((d for d in reversed(ds[:k]) if abs(gap(d) - 365) <= 45), None)
        if prev is None or yago is None or k < 3:
            continue
        last4 = ds[k - 3:k + 1]
        eps4 = [g("EPS in Rs", d) for d in last4]
        ttm_ok = 255 <= (d2(last4[-1]) - d2(last4[0])).days <= 290 and None not in eps4
        rev, npf, opp = [[g(lab, d) for d in (cur, prev, yago)] for lab in ("Sales", "Net Profit", "Operating Profit")]
        if None in rev or None in npf:
            continue
        eps0 = g("EPS in Rs", cur)
        rdate, src = ann.get(cur), "nse"
        if rdate is None or rdate <= cd or (rdate - cd).days > 120:
            rdate, src = spike_date(rows, cd), "spike"
        if rdate is None:
            continue
        before = [i for i in range(n) if dts[i] < rdate]
        after = [i for i in range(n) if dts[i] > rdate]
        if not before or not after:
            continue
        j0, i1 = before[-1], after[0]
        if (dts[i1] - rdate).days > 6:
            continue
        pre, c1 = rows[j0][2], rows[i1][2]
        base = sum(r[3] for r in rows[max(0, i1 - 20):i1]) / max(1, len(rows[max(0, i1 - 20):i1]))
        er = rows[i1][3] / base if base else float("nan")
        sc = score(rev, npf, [x if x is not None else float("nan") for x in opp], eps0 if eps0 is not None else float("nan"),
                   sum(eps4) if ttm_ok else float("nan"), pre, float("nan"), er)
        if sc is None:
            continue
        ev = {"sym": sym, "qend": cur, "rdate": rdate.isoformat(), "src": src, "total": round(sc[0], 1), "label": sc[1],
              "react": round((c1 / pre - 1) * 100, 2), "er": round(er, 2) if _ok(er) else None, "entry": dts[i1].isoformat()}
        for h in HORIZONS:
            if i1 + h < n:
                r = (rows[i1 + h][2] / c1 - 1) * 100
                n0, n1 = nifty_at(dts[i1]), nifty_at(dts[i1 + h])
                ev["r%d" % h] = round(r, 2)
                ev["x%d" % h] = round(r - (n1 / n0 - 1) * 100, 2) if n0 and n1 else None
        out.append(ev)
    return out


# ------------------------------------------------------------------ tables
def stats(vals, excess):
    vals = [v for v in vals if v is not None]
    ex = [v for v in excess if v is not None]
    if not vals:
        return {"n": 0}
    n = len(vals)
    o = {"n": n, "win": round(100 * sum(1 for v in vals if v > 0) / n, 1), "mean": round(st.mean(vals), 2), "median": round(st.median(vals), 2)}
    if ex:
        o["excess"] = round(st.mean(ex), 2)
        o["win_x"] = round(100 * sum(1 for v in ex if v > 0) / len(ex), 1)
        o["ci"] = round(1.96 * st.pstdev(ex) / math.sqrt(len(ex)), 2) if len(ex) > 1 else None   # about 95% range of the excess average
    return o


GROUPS = [
    ("All results", "every scored result", lambda e: True, 1),
    ("Excellent results", "score 80+", lambda e: e["label"] == "EXCELLENT", 1),
    ("Very good results", "score 65-79", lambda e: e["label"] == "VERY GOOD", 1),
    ("Good results", "score 45-64", lambda e: e["label"] == "GOOD", 1),
    ("Weak or poor results", "score under 45", lambda e: e["label"] in ("WEAK", "POOR"), 1),
    ("Positive reaction", "first session closed up", lambda e: e["react"] >= 0, 1),
    ("High volume", "first session volume 2x its 20-day average or more", lambda e: e["er"] is not None and e["er"] >= 2, 1),
    ("Excellent + positive reaction", "", lambda e: e["label"] == "EXCELLENT" and e["react"] >= 0, 1),
    ("Excellent + high volume", "", lambda e: e["label"] == "EXCELLENT" and e["er"] is not None and e["er"] >= 2, 1),
    ("YOUR COMBO: Excellent + high volume + positive reaction", "score 80+, volume 2x or more, first session up", lambda e: e["label"] == "EXCELLENT" and e["er"] is not None and e["er"] >= 2 and e["react"] >= 0, 1),
    ("Combo, looser: Excellent or Very good + volume 1.5x + positive", "score 65+", lambda e: e["label"] in ("EXCELLENT", "VERY GOOD") and e["er"] is not None and e["er"] >= 1.5 and e["react"] >= 0, 1),
    ("Combo, stricter: Excellent + volume 3x + reaction 2%+", "", lambda e: e["label"] == "EXCELLENT" and e["er"] is not None and e["er"] >= 3 and e["react"] >= 2, 1),
    ("SHORT side: Poor + high volume + negative reaction", "returns shown as if short (sign flipped)", lambda e: e["label"] in ("WEAK", "POOR") and e["er"] is not None and e["er"] >= 2 and e["react"] < 0, -1),
]


def aggregate(events):
    groups = []
    for name, desc, f, sign in GROUPS:
        sel = [e for e in events if f(e)]
        row = {"name": name, "desc": desc, "side": "short" if sign < 0 else "long", "events": len(sel)}
        for h in HORIZONS:
            row["h%d" % h] = stats([None if e.get("r%d" % h) is None else sign * e["r%d" % h] for e in sel], [None if e.get("x%d" % h) is None else sign * e["x%d" % h] for e in sel])
        groups.append(row)
    dates = sorted(e["rdate"] for e in events)
    return {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "events": len(events), "stocks": len({e["sym"] for e in events}),
            "from": dates[0] if dates else "", "to": dates[-1] if dates else "", "nse_dates": sum(1 for e in events if e["src"] == "nse"), "spike_dates": sum(1 for e in events if e["src"] == "spike"),
            "horizons": list(HORIZONS), "groups": groups,
            "note": "Return = from the close of the first session after the result to N trading days later; excess = minus the Nifty over the same days. Score is the PEAD Picks score re-created from Screener quarterly data (volume adjustment uses the first-session volume only). ci = about 95% range of the average excess. Fewer than 30 events is a rough guide only. Before brokerage and slippage."}


def write_outputs(events):
    res = aggregate(events)
    json.dump(res, open(OUT_JSON, "w"), separators=(",", ":"))
    cols = ["sym", "qend", "rdate", "src", "total", "label", "react", "er", "entry"] + [p + str(h) for h in HORIZONS for p in ("r", "x")]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(events)
    lines = [f"# PEAD back-test ({res['events']} results, {res['stocks']} stocks, {res['from']} to {res['to']})", "",
             f"Announcement dates: {res['nse_dates']} from NSE, {res['spike_dates']} from the volume spike.", "",
             "| Group | Events | 20d up | 20d avg | 20d vs Nifty | 60d avg | 60d vs Nifty |", "|---|---|---|---|---|---|---|"]
    for g in res["groups"]:
        a, b = g["h20"], g["h60"]
        lines.append(f"| {g['name']} | {g['events']} | {a.get('win', '-')}% | {a.get('mean', '-')}% | {a.get('excess', '-')}% | {b.get('mean', '-')}% | {b.get('excess', '-')}% |")
    open(OUT_MD, "w").write("\n".join(lines) + "\n\n" + res["note"] + "\n")
    return res


# ------------------------------------------------------------------ main
def main():
    cache = {}
    if os.path.exists(CACHE) and not os.environ.get("BT_REFRESH"):
        try: cache = json.load(open(CACHE))
        except Exception: cache = {}
    if "--aggregate" not in sys.argv:
        t0 = time.time()
        uni = [x.strip() for x in open(os.path.join(HERE, "universe.txt")) if x.strip()]
        random.Random(7).shuffle(uni)
        todo = [s for s in uni if s not in cache][:BT_MAX]
        print(f"{len(cache)} stocks cached, {len(todo)} to do this run")
        nifty = get_nifty()
        nse_start()
        scr_fail = 0
        for k, sym in enumerate(todo):
            if (time.time() - t0) / 60 > BUDGET_MIN:
                print("time budget reached, the next run continues")
                break
            P, why = get_screener(sym)
            if not P:
                print(f"  {sym}: skipped ({why})")
                cache[sym] = {"t": dt.date.today().isoformat(), "events": [], "why": why}
                scr_fail = scr_fail + 1 if why.startswith("http") else 0
                if scr_fail >= 5:
                    print("Screener is refusing requests, stopping; the next run continues")
                    break
                continue
            scr_fail = 0
            rows = get_hist(sym)
            if not rows:
                cache[sym] = {"t": dt.date.today().isoformat(), "events": [], "why": "no price history"}
                continue
            try:
                ev = stock_events(sym, P, rows, nifty, nse_dates(sym))
            except Exception as e:
                print(f"  {sym}: error {type(e).__name__}: {e}")
                ev = []
            cache[sym] = {"t": dt.date.today().isoformat(), "events": ev}
            if k % 25 == 0:
                json.dump(cache, open(CACHE, "w"), separators=(",", ":"))
                print(f"  {k + 1}/{len(todo)} done, {sum(len(v['events']) for v in cache.values())} events so far")
        json.dump(cache, open(CACHE, "w"), separators=(",", ":"))
    events = [e for v in cache.values() for e in v["events"]]
    res = write_outputs(events)
    print(f"wrote {res['events']} events from {res['stocks']} stocks")
    for g in res["groups"]:
        print(f"{g['name'][:62]:62s} n={g['events']:5d} 20d: {g['h20']}")


if __name__ == "__main__":
    main()
