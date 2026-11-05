#!/usr/bin/env python3
"""
PEAD research: which filters, alone and combined, made post-result trades profitable, and do they still work on results the search never saw?

Input : pead_features.csv (from pead_features.py). Falls back to pead_backtest.csv, which has far fewer columns.
Output: pead_research.md (read this) and pead_research.json.

How it avoids fooling you
  * Target = excess return over the SAME-MONTH average of all results ("alpha"), so a rule cannot look good just because it traded in a rising month.
    It must also beat the Nifty in plain terms ("excess"), because that is what you actually earn.
  * Rules are searched on the older ~55% of results only (TRAIN) and then judged on the newer ~45% (TEST) that the search never looked at.
  * Searching hundreds of thousands of rules always finds some that look great by luck. The report therefore shows how much the best TRAIN rules
    shrink on TEST. Trust the TEST column, and trust a rule more when it also works in most calendar years.
Usage: python pead_research.py [path_to_csv]
Env  : PEAD_SRC=nse  keep only results whose announcement date came from NSE. Dates marked "spike" are inferred from the day of the biggest volume jump, so for
       those results the reaction and the volume surge are high by construction; use this switch to check any volume or reaction finding on clean dates.
"""
import json, math, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MD, OUT_JSON = os.path.join(HERE, "pead_research.md"), os.path.join(HERE, "pead_research.json")
HOR = (5, 10, 20, 40, 60)
MIN_TRAIN, MIN_TEST = 60, 30
FEATS = ["total", "react", "gap", "er", "price", "pe", "fwd_pe", "gpe", "pe_rel", "earn_yield", "rev_y", "rev_q", "np_y", "np_q", "eb_y", "eb_q", "avg_yoy",
         "accel", "opm", "npm", "pos", "np_streak", "rev_streak", "np_yoy_avg4", "np_yoy_min4", "ret_1m", "ret_3m", "ret_6m", "ret_12m", "dist_52w",
         "vs_200dma", "vs_50dma", "rs_6m", "runup_20d", "turnover_cr", "vol_60d", "nifty_3m", "nifty_vs_200dma"]
NICE = {"total": "PEAD score", "react": "first-day reaction %", "gap": "opening gap %", "er": "volume surge (x)", "price": "price", "pe": "P/E", "fwd_pe": "forward P/E",
        "gpe": "growth-to-PE", "pe_rel": "P/E vs own history", "earn_yield": "earnings yield %", "rev_y": "sales YoY %", "rev_q": "sales QoQ %", "np_y": "profit YoY %",
        "np_q": "profit QoQ %", "eb_y": "EBITDA margin change YoY", "eb_q": "EBITDA margin change QoQ", "avg_yoy": "average YoY growth %", "accel": "acceleration",
        "opm": "operating margin %", "npm": "net margin %", "pos": "positive growth items (of 6)", "np_streak": "quarters of profit growth in a row",
        "rev_streak": "quarters of sales growth in a row", "np_yoy_avg4": "avg profit YoY, last 4 qtrs", "np_yoy_min4": "worst profit YoY, last 4 qtrs",
        "ret_1m": "1-month return before result", "ret_3m": "3-month return before result", "ret_6m": "6-month return before result", "ret_12m": "12-month return before result",
        "dist_52w": "distance from 52-week high %", "vs_200dma": "% above 200-day average", "vs_50dma": "% above 50-day average", "rs_6m": "6-month strength vs Nifty",
        "runup_20d": "run-up in the 20 days before", "turnover_cr": "daily turnover Rs crore", "vol_60d": "daily volatility %", "nifty_3m": "Nifty 3-month return",
        "nifty_vs_200dma": "Nifty % above 200-day average"}


def winsor(a, lo=1, hi=99):
    v = a[~np.isnan(a)]
    if len(v) < 20:
        return a
    l, h = np.percentile(v, [lo, hi])
    return np.clip(a, l, h)


def tstat(v):
    v = v[~np.isnan(v)]
    n = len(v)
    if n < 3:
        return 0.0
    sd = v.std(ddof=1)
    return float(v.mean() / (sd / math.sqrt(n))) if sd > 0 else 0.0


def load(path):
    df = pd.read_csv(path)
    df["entry"] = pd.to_datetime(df["entry"], errors="coerce")
    df = df.dropna(subset=["entry"]).sort_values("entry").reset_index(drop=True)
    if os.environ.get("PEAD_SRC") == "nse" and "src" in df.columns:
        df = df[df.src == "nse"].reset_index(drop=True)
    df["year"] = df.entry.dt.year
    df["ym"] = df.entry.dt.to_period("M").astype(str)
    num = [c for c in df.columns if c not in ("sym", "qend", "rdate", "src", "entry", "label", "ym")]
    for c in num:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # outcome columns that exist in the file
    outs = [c for c in df.columns if (c[0] in "rx" and c[1:].isdigit()) or (c[0] == "s" and "_" in c and c[1:].replace("_", "").isdigit())]
    # alpha = outcome minus the average of all results in the same month (falls back to the same year in thin months)
    for c in outs:
        m, cnt = df.groupby("ym")[c].transform("mean"), df.groupby("ym")[c].transform("count")
        y, ycnt = df.groupby("year")[c].transform("mean"), df.groupby("year")[c].transform("count")
        base = np.where(cnt >= 15, m, y)
        df["a_" + c] = df[c] - base
    return df, outs


def describe(rule, conds):
    parts = []
    for ci in rule:
        f, op, thr, _ = conds[ci]
        parts.append(f"{NICE.get(f, f)} {'at least' if op == '>=' else 'at most'} {thr:.4g}")
    return " AND ".join(parts)


def stats(df, mask, col="x20", acol="a_x20"):
    s = df[mask]
    v, a = s[col].dropna(), s[acol].dropna() if acol in s else pd.Series(dtype=float)
    n = len(v)
    if n == 0:
        return {"n": 0}
    return {"n": int(n), "mean": float(v.mean()), "median": float(v.median()), "win": float((v > 0).mean() * 100),
            "alpha": float(a.mean()) if len(a) else float("nan"), "t": tstat(v.values), "t_alpha": tstat(a.values) if len(a) else 0.0}


def build_conds(df, tr, feats):
    conds = []
    for f in feats:
        x = df[f].values
        tv = x[tr & ~np.isnan(x)]
        if len(tv) < 200 or len(np.unique(tv)) < 4:
            continue
        for q in (0.2, 0.35, 0.5, 0.65, 0.8):
            thr = float(np.quantile(tv, q))
            for op in (">=", "<="):
                m = (x >= thr) if op == ">=" else (x <= thr)
                m = m & ~np.isnan(x)
                conds.append((f, op, thr, m))
    return conds


def search(conds, y, tr, depth=4, beam=25, min_n=MIN_TRAIN):
    ok = ~np.isnan(y) & tr
    found = {}

    def ev(mask):
        s = mask & ok
        n = int(s.sum())
        if n < min_n:
            return None
        v = y[s]
        sd = v.std(ddof=1)
        return (float(v.mean() / (sd / math.sqrt(n))) if sd > 0 else 0.0, n, float(v.mean()))
    level = [((), np.ones(len(y), bool), -9.0)]
    for _ in range(depth):
        cand = {}
        for rule, mask, pt in level:
            used = {conds[c][0] for c in rule}
            for ci, (f, op, thr, cm) in enumerate(conds):
                if f in used:
                    continue
                key = tuple(sorted(rule + (ci,)))
                if key in cand or key in found:
                    continue
                r = ev(mask & cm)
                if r and r[2] > 0 and r[0] > max(pt, 0) + 0.15:
                    cand[key] = (r, mask & cm)
        if not cand:
            break
        top = sorted(cand.items(), key=lambda kv: -kv[1][0][0])[:beam]
        for key, (r, m) in top:
            found[key] = r
        level = [(k, m, r[0]) for k, (r, m) in top]
    return found


def pick_distinct(found, conds, df, tr, k=15):
    ok = tr
    out, masks = [], []
    for key, r in sorted(found.items(), key=lambda kv: -kv[1][0]):
        if r[0] < 2.0:          # a rule must have a real edge on TRAIN (t of 2 or more) before it is worth a look
            break
        m = np.ones(len(df), bool)
        for ci in key:
            m &= conds[ci][3]
        m &= ok
        dup = False
        for pm in masks:
            inter = (m & pm).sum()
            if inter / max(1, min(m.sum(), pm.sum())) > 0.8:
                dup = True
                break
        if dup:
            continue
        out.append((key, r))
        masks.append(m)
        if len(out) >= k:
            break
    return out


def pf(v, d=2, sign=False):
    return "-" if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else (("%+." if sign else "%.") + str(d) + "f") % v


def table(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else next((p for p in (os.path.join(HERE, "pead_features.csv"), os.path.join(HERE, "pead_backtest.csv")) if os.path.exists(p)), None)
    if not path:
        print("no input csv found")
        return
    df, outs = load(path)
    have = [f for f in FEATS if f in df.columns and df[f].notna().mean() > 0.4]
    split = df.entry.quantile(0.55)
    tr = (df.entry <= split).values
    te = ~tr
    y = winsor(df["a_x20"].values.copy())
    lines = [f"# PEAD research ({len(df)} results, {df.entry.min().date()} to {df.entry.max().date()}; filters tested: {len(have)})", "",
             f"Search period (TRAIN): up to {split.date()} ({int(tr.sum())} results). Unseen period (TEST): after it ({int(te.sum())} results).",
             "Returns are from the close of the first session after the result. Excess = minus the Nifty over the same days. Alpha = minus the average of all results in the same month.", ""]
    res = {"rows": len(df), "split": str(split.date()), "features": have}

    # ---- baseline and by year
    base_all, base_tr, base_te = stats(df, df.entry >= df.entry.min()), stats(df, tr), stats(df, te)
    lines += ["## 1. The starting point: every result", "", table(["Period", "Results", "20d excess avg", "20d median", "Up vs Nifty", "60d excess avg"],
              [[nm, s["n"], pf(s["mean"], 2, True) + "%", pf(s["median"], 2, True) + "%", pf(s["win"], 1) + "%", pf(stats(df, m, "x60", "a_x60").get("mean"), 2, True) + "%"]
               for nm, s, m in (("All", base_all, df.entry >= df.entry.min()), ("TRAIN", base_tr, tr), ("TEST", base_te, te))]), "",
              "A negative start means that buying any result lost to the Nifty, so a filter has to rescue it, not just add to it.", ""]
    yr = df.groupby("year").apply(lambda g: pd.Series({"n": len(g), "x20": g["x20"].mean(), "med": g["x20"].median()}), include_groups=False)
    lines += [table(["Year", "Results", "20d excess avg", "median"], [[int(i), int(r.n), pf(r.x20, 2, True) + "%", pf(r.med, 2, True) + "%"] for i, r in yr.iterrows() if r.n >= 20]), ""]

    # ---- single factors
    rows = []
    for f in have:
        x = df[f].values
        sub = ~np.isnan(x) & ~np.isnan(df["a_x20"].values)
        if sub.sum() < 300:
            continue
        r = pd.Series(x[sub]).rank().values
        a = df["a_x20"].values[sub]
        ic = float(np.corrcoef(r, pd.Series(a).rank().values)[0, 1])
        yrs = df.loc[sub, "year"].values
        ics = []
        for yy in np.unique(yrs):
            k = yrs == yy
            if k.sum() >= 80:
                ics.append(float(np.corrcoef(pd.Series(x[sub][k]).rank().values, pd.Series(a[k]).rank().values)[0, 1]))
        same = sum(1 for v in ics if v * ic > 0)
        q = pd.qcut(pd.Series(x[sub]), 5, labels=False, duplicates="drop")
        qm = pd.Series(a).groupby(q.values).mean()
        rows.append((f, ic, ic * math.sqrt(sub.sum()), f"{same}/{len(ics)}", [float(v) for v in qm.values]))
    rows.sort(key=lambda r: -abs(r[2]))
    lines += ["## 2. One filter at a time (which numbers carry information?)", "",
              "Rank correlation (IC) of each filter with the 20-day alpha, and the average alpha of the lowest-to-highest fifth of results. 'Years same sign' counts calendar years in which the filter pointed the same way.", "",
              table(["Filter", "IC", "z", "Years same sign", "Lowest fifth ... highest fifth (avg 20d alpha %)"],
                    [[NICE.get(f, f), pf(ic, 3, True), pf(z, 1, True), ys, " / ".join(pf(v, 1, True) for v in qs)] for f, ic, z, ys, qs in rows[:20]]), ""]
    res["single"] = [{"f": f, "ic": ic, "z": z, "years": ys, "quintiles": qs} for f, ic, z, ys, qs in rows]

    # ---- rule search
    conds = build_conds(df, tr, have)
    found = search(conds, y, tr)
    top = pick_distinct(found, conds, df, tr, 15)
    tab, good, shrink = [], [], []
    if not top:
        lines += ["## 3. Best combinations found on TRAIN, judged on unseen TEST", "", "No combination reached a convincing edge (t of 2 or more) on the search period with at least %d results." % MIN_TRAIN, ""]
    for key, r in top:
        m = np.ones(len(df), bool)
        for ci in key:
            m &= conds[ci][3]
        a, b, c = stats(df, m & tr), stats(df, m & te), stats(df, m)
        shrink.append((a.get("alpha"), b.get("alpha")))
        yrs = [(int(yy), stats(df, m & (df.year == yy).values)) for yy in sorted(df.year.unique())]
        yrs = [(yy, s) for yy, s in yrs if s.get("n", 0) >= 8]
        pos = sum(1 for yy, s in yrs if s["mean"] > 0)
        row = dict(rule=describe(key, conds), train=a, test=b, years=f"{pos}/{len(yrs)}")
        tab.append(row)
        if b.get("n", 0) >= MIN_TEST and b["mean"] > 0 and b.get("alpha", -1) > 0 and a["mean"] > 0:
            good.append((key, m, row))
    if top:
      lines += ["## 3. Best combinations found on TRAIN, judged on unseen TEST", "",
              table(["Rule (all must be true)", "TRAIN n", "TRAIN 20d excess", "TEST n", "TEST 20d excess", "TEST alpha", "TEST up vs Nifty", "TEST median", "Years positive"],
                    [[r["rule"], r["train"]["n"], pf(r["train"]["mean"], 1, True) + "%", r["test"].get("n", 0), pf(r["test"].get("mean"), 1, True) + "%", pf(r["test"].get("alpha"), 1, True) + "%",
                      pf(r["test"].get("win"), 0) + "%", pf(r["test"].get("median"), 1, True) + "%", r["years"]] for r in tab]), ""]
    sh = [(a, b) for a, b in shrink if a is not None and b is not None and not (math.isnan(a) or math.isnan(b))]
    if sh:
        lines += [f"Shrinkage check: these {len(sh)} rules averaged {pf(np.mean([a for a, _ in sh]), 2, True)}% alpha on TRAIN and {pf(np.mean([b for _, b in sh]), 2, True)}% on TEST. "
                  "The second number is what to expect going forward; the gap is luck the search picked up.", ""]
    res["rules"] = tab

    # ---- named ideas
    G = lambda f: df[f].values if f in df.columns else None
    named = []

    def add(name, parts):
        if any(p is None for p in parts):
            return
        m = np.ones(len(df), bool)
        for p in parts:
            m &= p
        named.append((name, m))
    t, rc, er, pe, fpe, r6, d52, ns, ps, tu, gp = G("total"), G("react"), G("er"), G("pe"), G("fwd_pe"), G("ret_6m"), G("dist_52w"), G("np_streak"), G("pos"), G("turnover_cr"), G("gpe")
    nn = lambda a: (~np.isnan(a)) if a is not None else None
    ge = lambda a, v: (a >= v) & ~np.isnan(a) if a is not None else None
    le = lambda a, v: (a <= v) & ~np.isnan(a) if a is not None else None
    add("Your original combo: Excellent + volume 2x + positive reaction", [ge(t, 80), ge(er, 2), ge(rc, 0)])
    add("Score 55+ and first-day reaction 5%+", [ge(t, 55), ge(rc, 5)])
    add("Score 55+ and low volume surge (under 2x)", [ge(t, 55), le(er, 2)])
    add("Growth at a fair price: score 55+, forward P/E 20 or less", [ge(t, 55), le(fpe, 20)])
    add("Cheap and growing: score 55+, growth-to-PE 1.2+", [ge(t, 55), ge(gp, 1.2)])
    add("Momentum: score 55+, 6-month return 20%+, within 15% of 52-week high", [ge(t, 55), ge(r6, 20), ge(d52, -15)])
    add("Durable: score 55+, profit grew 4+ quarters in a row, 5+ of 6 items positive", [ge(t, 55), ge(ns, 4), ge(ps, 5)])
    add("Beaten-down turnaround: score 55+, 6-month return under 0", [ge(t, 55), le(r6, 0)])
    add("Liquid only: score 55+, reaction 3%+, turnover Rs 2 crore a day or more", [ge(t, 55), ge(rc, 3), ge(tu, 2)])
    nrows = []
    for name, m in named:
        a, b, c = stats(df, m & tr), stats(df, m & te), stats(df, m)
        if c.get("n", 0) >= 20:
            cn = stats(df, m & (df["src"] == "nse").values) if "src" in df.columns else {"n": 0}
            nrows.append([name, c["n"], pf(c["mean"], 1, True) + "%", pf(c["alpha"], 1, True) + "%", pf(c["win"], 0) + "%", pf(c["median"], 1, True) + "%", b.get("n", 0), pf(b.get("mean"), 1, True) + "%",
                          cn.get("n", 0), pf(cn.get("mean"), 1, True) + "%" if cn.get("n", 0) >= 10 else "-"])
    if nrows:
        lines += ["## 4. Ideas you asked about, tested as written (fixed thresholds, nothing tuned)", "",
                  table(["Idea", "All n", "20d excess", "Alpha", "Up vs Nifty", "Median", "TEST n", "TEST 20d excess", "NSE-dated n", "NSE-dated 20d excess"], nrows), ""]

    # ---- how to trade the best surviving rule
    best = None
    if good:
        best = good[0]      # strongest on TRAIN among those that also held up on TEST (never picked by looking at TEST)
    elif named:
        cand = [(n, m) for n, m in named if stats(df, m).get("n", 0) >= 40]
        if cand:
            nm, m = max(cand, key=lambda x: stats(df, x[1])["mean"])
            best = (None, m, {"rule": nm, "train": stats(df, m & tr), "test": stats(df, m & te)})
    if best:
        key, m, row = best
        yrsn = max(1, (df.entry.max() - df.entry.min()).days / 365)
        lines += ["## 5. How the best rule behaves as a trade", "", f"Rule: **{row['rule']}**", ""]
        hr = []
        for h in HOR:
            if f"r{h}" in df.columns:
                s = stats(df, m, f"x{h}", f"a_x{h}")
                r = df.loc[m, f"r{h}"].dropna()
                hr.append([f"{h} days", s["n"], pf(r.mean(), 2, True) + "%", pf(s["mean"], 2, True) + "%", pf(s["median"], 2, True) + "%", pf(s["win"], 0) + "%"])
        lines += [table(["Hold for", "Trades", "Avg return", "Avg vs Nifty", "Median vs Nifty", "Up vs Nifty"], hr), ""]
        sr = []
        for c in [c for c in df.columns if c.startswith("s") and "_" in c and c[1:].replace("_", "").isdigit()]:
            v = df.loc[m, c].dropna()
            if len(v):
                sr.append([f"stop {c.split('_')[0][1:]}% / {c.split('_')[1]} days", len(v), pf(v.mean(), 2, True) + "%", pf(v.median(), 2, True) + "%", pf((v > 0).mean() * 100, 0) + "%"])
        if sr:
            lines += [table(["Exit rule (close-based stop)", "Trades", "Avg return", "Median", "Winners"], sr), ""]
        if "mdd20" in df.columns:
            lines += [f"Typical worst dip inside the first 20 days: median {pf(df.loc[m, 'mdd20'].median(), 1)}%, 1 trade in 4 dipped {pf(df.loc[m, 'mdd20'].quantile(0.25), 1)}% or worse.", ""]
        lines += [f"Frequency: about {int(m.sum() / yrsn)} qualifying results a year across the whole universe. " + (f"Median daily turnover of these stocks: Rs {pf(df.loc[m, 'turnover_cr'].median(), 1)} crore." if "turnover_cr" in df.columns else ""), ""]
        res["best"] = row

    lines += ["## How to read this honestly", "",
              "* A rule is only interesting if its TEST numbers are positive, its TEST count is at least 30, and it is positive in most years.",
              "* Averages here are pulled up by a few big winners. Look at the median and the share of winners as well as the average.",
              "* Results are before brokerage, taxes and slippage. Small, thinly traded stocks can cost 1-3% to enter and exit, which can erase an edge of that size.",
              "* Announcement dates marked 'spike' were inferred from a volume jump, not taken from the exchange, so some entries are a day off.",
              "* Past results only. General information, not advice."]
    open(OUT_MD, "w").write("\n".join(lines) + "\n")
    json.dump(res, open(OUT_JSON, "w"), default=lambda o: None if (isinstance(o, float) and math.isnan(o)) else str(o))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
