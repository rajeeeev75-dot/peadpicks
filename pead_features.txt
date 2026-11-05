#!/usr/bin/env python3
"""
PEAD research data: the same past results as pead_backtest.py, but every event also carries the numbers you want to test as filters
(valuation, growth, durability, momentum, liquidity, market state) and richer outcomes (5/10/20/40/60-day returns, worst dip, stop-loss results).

Everything used as a filter is known BEFORE the entry (the close of the first session after the result), so a rule found in
pead_research.py could really have been traded. Momentum uses prices up to the close before the result, so it is not mixed up with the reaction.

Output (next to pead.csv): pead_features.csv (one row per result) and features_cache.json (resume file; a run picks up where the last one stopped).
Usage:   python pead_features.py            (stops after BUDGET_MIN minutes, resumes next time)
         python pead_features.py --aggregate (only rewrite the CSV from the cache)
Env:     BT_MAX (stocks per run, default 500)  BUDGET_MIN (default 100)  BT_REFRESH=1 (ignore the cache)
"""
import bisect, csv, json, math, os, random, statistics as st, sys, time, datetime as dt

import pead_backtest as B
from pead_backtest import _ok, nz, clamp, pgrow, d2

HERE = B.HERE
CACHE = os.path.join(HERE, "features_cache.json")
OUT_CSV = os.path.join(HERE, "pead_features.csv")
HOR = (5, 10, 20, 40, 60)
STOPS = ((8, 20), (12, 20), (8, 60), (12, 60))      # (stop %, holding days)
BUDGET_MIN = float(os.environ.get("BUDGET_MIN", "100"))
BT_MAX = int(os.environ.get("BT_MAX", "500"))

COLS = (["sym", "qend", "rdate", "src", "entry", "total", "label", "react", "gap", "er",
         # valuation
         "price", "pe", "fwd_pe", "gpe", "pe_rel", "earn_yield",
         # growth and quality of the quarter
         "rev_y", "rev_q", "np_y", "np_q", "eb_y", "eb_q", "avg_yoy", "accel", "opm", "npm",
         # durability
         "pos", "np_streak", "rev_streak", "np_yoy_avg4", "np_yoy_min4",
         # momentum before the result
         "ret_1m", "ret_3m", "ret_6m", "ret_12m", "dist_52w", "vs_200dma", "vs_50dma", "rs_6m", "runup_20d",
         # tradability and risk
         "turnover_cr", "vol_60d",
         # market state
         "nifty_3m", "nifty_vs_200dma"]
        + [p + str(h) for h in HOR for p in ("r", "x")] + ["mdd20", "mfe20"] + ["s%d_%d" % s for s in STOPS])


def pct(a, b):
    return (a / b - 1) * 100 if b else float("nan")


def derive(rev, npf, opp, eps0, eps_ttm, price):
    """Growth, margin, forward P/E and growth-to-PE, worked out exactly as score() does (auto forward P/E mode)."""
    mar = lambda i: nz(opp[i]) / nz(rev[i]) * 100 if nz(rev[i]) != 0 else 0.0
    rev_q, rev_y, np_q, np_y = pgrow(rev[0], rev[1]), pgrow(rev[0], rev[2]), pgrow(npf[0], npf[1]), pgrow(npf[0], npf[2])
    eb_q, eb_y = mar(0) - mar(1), mar(0) - mar(2)
    avg_yoy = (rev_y + np_y + eb_y) / 3
    capped = clamp(avg_yoy, 0, 60)
    ttm = eps_ttm if _ok(eps_ttm) and eps_ttm != 0 else 0
    runrate = eps0 * 4 if nz(eps0) > 0 else 0
    pead_e = ttm * (1 + capped / 100) if ttm > 0 else 0
    fwd = max(runrate, pead_e)
    fwd_pe = price / fwd if fwd > 0 and _ok(price) else float("nan")
    gpe = capped / fwd_pe if _ok(fwd_pe) and fwd_pe > 0 else float("nan")
    avg_q = (rev_q + np_q + eb_q) / 3
    pos = sum(1 for x in (rev_y, rev_q, np_y, np_q, eb_y, eb_q) if x > 0)
    return dict(rev_y=rev_y, rev_q=rev_q, np_y=np_y, np_q=np_q, eb_y=eb_y, eb_q=eb_q, avg_yoy=avg_yoy, accel=avg_yoy - abs(avg_q) * 4,
                fwd_pe=fwd_pe, gpe=gpe, pos=pos, opm=mar(0), npm=nz(npf[0]) / nz(rev[0]) * 100 if nz(rev[0]) != 0 else float("nan"))


def stock_events_v2(sym, P, rows, nifty, ann):
    q, ds = P["q"], P["dates"]
    g = lambda lab, d: (q.get(lab) or {}).get(d)
    n = len(rows)
    dts = [r[0] for r in rows]
    op, cl, vo = [r[1] for r in rows], [r[2] for r in rows], [r[3] for r in rows]
    nd = sorted(nifty)
    ncl = [nifty[d] for d in nd]

    def nidx(d):                       # index of the last Nifty day on or before d
        i = bisect.bisect_right(nd, d) - 1
        return i if i >= 0 else None

    def yoy_of(m, label):              # year-on-year growth of quarter m (None if the year-ago quarter is missing)
        cd = d2(ds[m])
        ya = next((d for d in reversed(ds[:m]) if abs((cd - d2(d)).days - 365) <= 45), None)
        a, b = g(label, ds[m]), (g(label, ya) if ya else None)
        return pgrow(a, b) if a is not None and b is not None else None

    def streak(k, label):
        s = 0
        for m in range(k, max(-1, k - 8), -1):
            y = yoy_of(m, label)
            if y is None or y <= 0:
                break
            s += 1
        return s

    def ttm_at(m):
        if m < 3:
            return None
        last4 = ds[m - 3:m + 1]
        e4 = [g("EPS in Rs", d) for d in last4]
        if None in e4 or not (255 <= (d2(last4[-1]) - d2(last4[0])).days <= 290):
            return None
        return sum(e4)

    def close_on(d):                   # close on or before d
        i = bisect.bisect_right(dts, d) - 1
        return cl[i] if i >= 0 else None

    out = []
    for k, cur in enumerate(ds):
        cd = d2(cur)
        gap = lambda d: (cd - d2(d)).days
        prev = next((d for d in reversed(ds[:k]) if 60 <= gap(d) <= 125), None)
        yago = next((d for d in reversed(ds[:k]) if abs(gap(d) - 365) <= 45), None)
        if prev is None or yago is None or k < 3:
            continue
        eps_ttm = ttm_at(k)
        rev, npf, opp = [[g(lab, d) for d in (cur, prev, yago)] for lab in ("Sales", "Net Profit", "Operating Profit")]
        if None in rev or None in npf:
            continue
        eps0 = g("EPS in Rs", cur)
        rdate, src = ann.get(cur), "nse"
        if rdate is None or rdate <= cd or (rdate - cd).days > 120:
            rdate, src = B.spike_date(rows, cd), "spike"
        if rdate is None:
            continue
        before = [i for i in range(n) if dts[i] < rdate]
        after = [i for i in range(n) if dts[i] > rdate]
        if not before or not after:
            continue
        j0, i1 = before[-1], after[0]
        if (dts[i1] - rdate).days > 6:
            continue
        pre, c1 = cl[j0], cl[i1]
        window = vo[max(0, i1 - 20):i1]
        base = sum(window) / max(1, len(window))
        er = vo[i1] / base if base else float("nan")
        opp2 = [x if x is not None else float("nan") for x in opp]
        sc = B.score(rev, npf, opp2, eps0 if eps0 is not None else float("nan"), eps_ttm if eps_ttm is not None else float("nan"), pre, float("nan"), er)
        if sc is None:
            continue
        D = derive(rev, npf, opp2, eps0 if eps0 is not None else float("nan"), eps_ttm if eps_ttm is not None else float("nan"), pre)
        pe = pre / eps_ttm if eps_ttm and eps_ttm > 0 else float("nan")
        # P/E now against this stock's own P/E at the last 8 results (valuation relative to its history)
        hist = []
        for m in range(max(3, k - 8), k):
            e = ttm_at(m)
            p = close_on(d2(ds[m]) + dt.timedelta(days=45))
            if e and e > 0 and p and d2(ds[m]) + dt.timedelta(days=45) < rdate:
                hist.append(p / e)
        pe_rel = pe / st.median(hist) if _ok(pe) and len(hist) >= 4 and st.median(hist) > 0 else float("nan")
        n4 = [y for y in (yoy_of(m, "Net Profit") for m in range(max(0, k - 3), k + 1)) if y is not None]
        ret = lambda d: pct(cl[j0], cl[j0 - d]) if j0 >= d else float("nan")
        hi52 = max(cl[max(0, j0 - 251):j0 + 1])
        ma = lambda d: sum(cl[j0 - d + 1:j0 + 1]) / d if j0 >= d - 1 else float("nan")
        ni = nidx(dts[j0])
        n3 = pct(ncl[ni], ncl[ni - 63]) if ni is not None and ni >= 63 else float("nan")
        n6 = pct(ncl[ni], ncl[ni - 126]) if ni is not None and ni >= 126 else float("nan")
        n200 = sum(ncl[ni - 199:ni + 1]) / 200 if ni is not None and ni >= 199 else float("nan")
        r126 = ret(126)
        daily = [cl[i] / cl[i - 1] - 1 for i in range(max(1, j0 - 59), j0 + 1)]
        turn = [cl[i] * vo[i] for i in range(max(0, j0 - 19), j0 + 1)]
        ev = {"sym": sym, "qend": cur, "rdate": rdate.isoformat(), "src": src, "entry": dts[i1].isoformat(), "total": round(sc[0], 1), "label": sc[1],
              "react": pct(c1, pre), "gap": pct(op[i1], pre), "er": er, "price": pre, "pe": pe, "fwd_pe": D["fwd_pe"], "gpe": D["gpe"], "pe_rel": pe_rel,
              "earn_yield": 100 / pe if _ok(pe) and pe > 0 else float("nan"),
              "rev_y": D["rev_y"], "rev_q": D["rev_q"], "np_y": D["np_y"], "np_q": D["np_q"], "eb_y": D["eb_y"], "eb_q": D["eb_q"], "avg_yoy": D["avg_yoy"],
              "accel": D["accel"], "opm": D["opm"], "npm": D["npm"], "pos": D["pos"], "np_streak": streak(k, "Net Profit"), "rev_streak": streak(k, "Sales"),
              "np_yoy_avg4": clamp(sum(n4) / len(n4), -100, 300) if n4 else float("nan"), "np_yoy_min4": clamp(min(n4), -100, 300) if n4 else float("nan"),
              "ret_1m": ret(21), "ret_3m": ret(63), "ret_6m": r126, "ret_12m": ret(252), "dist_52w": pct(cl[j0], hi52),
              "vs_200dma": pct(cl[j0], ma(200)) if j0 >= 199 else float("nan"), "vs_50dma": pct(cl[j0], ma(50)) if j0 >= 49 else float("nan"),
              "rs_6m": r126 - n6 if _ok(r126) and _ok(n6) else float("nan"), "runup_20d": ret(20),
              "turnover_cr": sum(turn) / len(turn) / 1e7, "vol_60d": st.pstdev(daily) * 100 if len(daily) >= 30 else float("nan"),
              "nifty_3m": n3, "nifty_vs_200dma": pct(ncl[ni], n200) if ni is not None and _ok(n200) else float("nan")}
        for h in HOR:
            if i1 + h < n:
                r = pct(cl[i1 + h], c1)
                a, b = nidx(dts[i1]), nidx(dts[i1 + h])
                ev["r%d" % h] = r
                ev["x%d" % h] = r - pct(ncl[b], ncl[a]) if a is not None and b is not None and a != b else float("nan")
        if i1 + 20 < n:
            path = [pct(cl[i1 + d], c1) for d in range(1, 21)]
            ev["mdd20"], ev["mfe20"] = min(path), max(path)
        for stop, hold in STOPS:                       # close-based stop: leave at the first close that is stop% below the entry close
            if i1 + hold < n:
                res = pct(cl[i1 + hold], c1)
                for d in range(1, hold + 1):
                    r = pct(cl[i1 + d], c1)
                    if r <= -stop:
                        res = r
                        break
                ev["s%d_%d" % (stop, hold)] = res
        out.append(ev)
    return out


def fmt(v):
    if isinstance(v, float):
        return "" if math.isnan(v) or math.isinf(v) else round(v, 3)
    return "" if v is None else v


def write_csv(events):
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        for e in events:
            w.writerow({c: fmt(e.get(c)) for c in COLS})


def main():
    cache = {}
    if os.path.exists(CACHE) and not os.environ.get("BT_REFRESH"):
        try:
            cache = json.load(open(CACHE))
        except Exception:
            cache = {}
    if "--aggregate" not in sys.argv:
        t0 = time.time()
        uni = [x.strip() for x in open(os.path.join(HERE, "universe.txt")) if x.strip()]
        random.Random(7).shuffle(uni)
        todo = [s for s in uni if s not in cache][:BT_MAX]
        print(f"{len(cache)} stocks cached, {len(todo)} to do this run")
        nifty = B.get_nifty()
        B.nse_start()
        scr_fail = 0
        for k, sym in enumerate(todo):
            if (time.time() - t0) / 60 > BUDGET_MIN:
                print("time budget reached, the next run continues")
                break
            P, why = B.get_screener(sym)
            if not P:
                print(f"  {sym}: skipped ({why})")
                cache[sym] = {"t": dt.date.today().isoformat(), "events": [], "why": why}
                scr_fail = scr_fail + 1 if why.startswith("http") else 0
                if scr_fail >= 5:
                    print("Screener is refusing requests, stopping; the next run continues")
                    break
                continue
            scr_fail = 0
            rows = B.get_hist(sym)
            if not rows:
                cache[sym] = {"t": dt.date.today().isoformat(), "events": [], "why": "no price history"}
                continue
            try:
                ev = stock_events_v2(sym, P, rows, nifty, B.nse_dates(sym))
            except Exception as e:
                print(f"  {sym}: error {type(e).__name__}: {e}")
                ev = []
            cache[sym] = {"t": dt.date.today().isoformat(), "events": [{k: fmt(v) if isinstance(v, float) else v for k, v in e.items()} for e in ev]}
            if k % 25 == 0:
                json.dump(cache, open(CACHE, "w"), separators=(",", ":"))
                print(f"  {k + 1}/{len(todo)} done, {sum(len(v['events']) for v in cache.values())} events so far")
        json.dump(cache, open(CACHE, "w"), separators=(",", ":"))
    events = [e for v in cache.values() for e in v["events"]]
    write_csv(events)
    print(f"wrote {len(events)} events from {sum(1 for v in cache.values() if v['events'])} stocks to {OUT_CSV}")


if __name__ == "__main__":
    main()
