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
import csv, io, json, os, re, sys, time, datetime as dt
import warnings
import requests, pandas as pd, yfinance as yf

warnings.filterwarnings("ignore")   # hides the harmless yfinance/pandas deprecation spam in the Action log

RECENT_DAYS = 14        # "just announced" = results filed in the last N days
KEEP_DAYS = 45          # (kept for reference)
QTR_MAX_AGE = 120       # ignore stocks whose newest quarter is older than this (days)
CR = 1e7
MCAP_MAX_CR = float(os.environ.get("MCAP_MAX_CR", "0"))   # 0 = no market-cap filter (every NSE stock is scored); set e.g. 50000 to skip very large caps
BUDGET_MIN = float(os.environ.get("BUDGET_MIN", "100"))       # stop scanning after this many minutes; the rest is picked up by the next run
WORKER = os.environ.get("WORKER_URL", "https://market-feed.rajeeeev75.workers.dev")
RECHECK = {"ok": 7, "big": 30, "nodata": 14, "stale": 25}   # "stale" = newest quarter is old, i.e. the company has not reported yet; re-opened early when the Worker calendar shows a new filing                  # days before a stock is looked at again (full runs)
COLS = ["ticker","name","price","mcap","pe","high52","result_date","quarter_end",
        "rev_cur","rev_prev","rev_yoy","np_cur","np_prev","np_yoy",
        "ebitda_cur","ebitda_prev","ebitda_yoy","eps_cur","eps_prev","eps_yoy",
        "eps_ttm","np_ttm","equity","debt","bvps","earn_ratio","vol_ratio","above_ema200",
        "feed_note"]


class Skip(Exception):
    """Raised with a human-readable reason when a stock cannot be (re)built."""


FILING_KEYS = ("broadcast", "exchdiss", "disseminat", "filingdate", "filing_date", "filing", "submission")
SKIP_KEYS = ("fromdate", "from_date", "todate", "to_date", "period", "audit", "xbrl", "attachment")
QEND = {(3, 31), (6, 30), (9, 30), (12, 31)}


def is_qend(d):
    return (d.month, d.day) in QEND


def filing_date(row):
    """The day the company filed its results, from one NSE row. Looks at the broadcast / filing
    style keys in priority order and ignores quarter-end dates (30-Sep etc.), which are the
    period the results cover, not the day they were announced."""
    found = []
    for k, v in row.items():
        kl = k.lower()
        if any(x in kl for x in SKIP_KEYS) or not any(x in kl for x in FILING_KEYS):
            continue
        d = pd.to_datetime(v, dayfirst=True, errors="coerce")
        if pd.isna(d) or is_qend(d.date()):
            continue
        found.append((min(i for i, x in enumerate(FILING_KEYS) if x in kl), d.date()))
    return min(found)[1] if found else None


def valid_rd(text, qend):
    """An old result_date from pead.csv is only trusted if it is a real day after the quarter end."""
    d = pd.to_datetime(text, dayfirst=True, errors="coerce")
    if pd.isna(d) or is_qend(d.date()):
        return None
    return d.date() if not qend or d.date() > dt.date.fromisoformat(qend) else None


NSE = {"s": None, "h": None, "feed": {}, "calls": 0}


def feed_add(rows):
    """Remember every NSE row as {(symbol, quarter end): earliest filing date}, so any stock's real
    announcement date can be looked up by the quarter it reports."""
    for row in rows:
        sym, q = row.get("symbol"), pd.to_datetime(row.get("toDate"), dayfirst=True, errors="coerce")
        d = filing_date(row)
        if sym and d and not pd.isna(q):
            k = (sym, q.date().isoformat())
            if k not in NSE["feed"] or d < NSE["feed"][k]:
                NSE["feed"][k] = d


def nse_filing_for(sym, qend):
    """Real announcement date of one stock's quarter: from the big feed if present, else one
    per-stock request (NSE's website does the same). Returns a date or None."""
    d = NSE["feed"].get((sym, qend))
    if d or NSE["s"] is None or NSE["calls"] >= 250:
        return d
    NSE["calls"] += 1
    try:
        r = NSE["s"].get("https://www.nseindia.com/api/corporates-financial-results?index=equities&symbol=" + requests.utils.quote(sym) + "&period=Quarterly", headers=NSE["h"], timeout=20)
        r.raise_for_status()
        rows = r.json()
        feed_add(rows if isinstance(rows, list) else rows.get("data", []))
    except Exception as e:
        print(f"  NSE per-stock date lookup failed for {sym}: {e}", file=sys.stderr)
    return NSE["feed"].get((sym, qend))


def nse_recent():
    """Best effort: {symbol: filing_date} from NSE's financial-results feed. Tries the date-range form
    first (what NSE's own website uses), then the plain form, and keeps whichever gives results. Prints
    what it saw so the Action log shows exactly why a date is missing. If NSE gives nothing we fall
    back to tickers.txt and detect new quarters from the data itself."""
    out = {}
    try:
        s = requests.Session()
        h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-financial-results"}
        s.get("https://www.nseindia.com", headers=h, timeout=20)
        s.get("https://www.nseindia.com/companies-listing/corporate-filings-financial-results", headers=h, timeout=20)
        NSE["s"], NSE["h"] = s, h
        today = dt.date.today(); cut = today - dt.timedelta(days=RECENT_DAYS)
        fmt = lambda d: d.strftime("%d-%m-%Y")
        urls = [
            f"https://www.nseindia.com/api/corporates-financial-results?index=equities&from_date={fmt(cut)}&to_date={fmt(today)}&period=Quarterly",
            "https://www.nseindia.com/api/corporates-financial-results?index=equities&period=Quarterly",
        ]
        for u in urls:
            try:
                r = s.get(u, headers=h, timeout=30)
                r.raise_for_status()
                rows = r.json()
                rows = rows if isinstance(rows, list) else rows.get("data", [])
            except Exception as e:
                print("NSE feed attempt failed:", u.split("?")[1][:60], "->", e, file=sys.stderr)
                continue
            feed_add(rows)
            got = {}
            for row in rows:
                sym = row.get("symbol")
                d = filing_date(row)
                if sym and d and d >= cut and (sym not in got or d > got[sym]):
                    got[sym] = d
            print(f"NSE feed ({u.split('?')[1][:40]}...): {len(rows)} rows, {len(got)} filed since {cut}", file=sys.stderr)
            if NSE["feed"]:
                ds = sorted(NSE["feed"].values())
                print(f"NSE feed dates: {len(NSE['feed'])} stock-quarters, filings from {ds[0]} to {ds[-1]}", file=sys.stderr)
            if rows:
                print("NSE sample:", {k: rows[0].get(k) for k in ("symbol", "broadCastDate", "filingDate", "exchdisstime", "fromDate", "toDate")}, file=sys.stderr)
            if len(got) > len(out):
                out = got
            if out:
                break
    except Exception as e:
        print("NSE feed unavailable:", e, file=sys.stderr)
    return out


class Big(Exception):
    pass


def nse_universe():
    """Every NSE equity symbol (series EQ/BE/SM/ST). Cached in universe.txt so a failed download
    never shrinks the list."""
    urls = ["https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv", "https://archives.nseindia.com/content/equities/EQUITY_L.csv"]
    got = []
    for u in urls:
        try:
            r = requests.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=40)
            r.raise_for_status()
            rd = csv.DictReader(io.StringIO(r.text))
            for row in rd:
                row = {(k or "").strip().upper(): (v or "").strip() for k, v in row.items()}
                if row.get("SERIES") in ("EQ", "BE", "SM", "ST") and row.get("SYMBOL"):
                    got.append(row["SYMBOL"].upper())
            if len(got) > 1000:
                break
        except Exception as e:
            print("NSE equity list failed:", u, "->", e, file=sys.stderr)
            got = []
    if len(got) > 1000:
        got = sorted(set(got))
        open("universe.txt", "w").write("\n".join(got) + "\n")
        print(f"NSE equity list: {len(got)} symbols (saved to universe.txt)")
        return got
    if os.path.exists("universe.txt"):
        got = [x.strip() for x in open("universe.txt") if x.strip()]
        print(f"NSE equity list unavailable, using cached universe.txt ({len(got)} symbols)")
    return got


def worker_results():
    """{symbol: date} of results announced in the last 60 days, from your Worker's NSE board-meeting
    calendar (?results=1). Works from GitHub where NSE's own results feed returns stale rows."""
    out = {}
    try:
        r = requests.get(WORKER + "/?results=1", timeout=60)
        r.raise_for_status()
        for x in r.json().get("results", []):
            try:
                out[x["s"].upper()] = dt.date.fromisoformat(x["d"][:10])
            except Exception:
                pass
        print(f"Worker calendar: {len(out)} companies announced results in the last 60 days")
    except Exception as e:
        print("Worker calendar unavailable:", e, file=sys.stderr)
    return out


def load_state():
    try:
        return json.load(open("scan_state.json"))
    except Exception:
        return {}


# ---------------------------------------------------------------------------------------------
# Screener.in fallback. Yahoo updates Indian quarterly results slowly (days to weeks) and misses many
# small caps; Screener shows a result within about a day. Used only when Yahoo has no usable / no newer quarter
# for a company that has just announced results (or one of yours).
# ---------------------------------------------------------------------------------------------
SCR = {"off": False, "n": 0, "fail429": 0}
SCR_MAX = int(os.environ.get("SCREENER_MAX", "900"))
SCR_HEAD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleScreener/1.0 Chrome/124 Safari/537.36", "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-IN,en;q=0.9"}


def _txt(x):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).replace("&nbsp;", " ").replace("&amp;", "&").strip()


def _num(x):
    x = (x or "").replace(",", "").replace("%", "").replace("\u20b9", "").strip()
    try:
        return float(x)
    except Exception:
        return None


def scr_table(html, sec_id):
    """{row label: {date 'YYYY-MM-DD': value}} for one section of a Screener page."""
    m = re.search(r'<section id="%s".*?</section>' % sec_id, html, re.S)
    if not m:
        return {}
    sec = m.group(0)
    head = re.search(r"<thead>(.*?)</thead>", sec, re.S)
    if not head:
        return {}
    keys = re.findall(r'data-date-key="([^"]+)"', head.group(1))
    out = {}
    body = re.search(r"<tbody>(.*?)</tbody>", sec, re.S)
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body.group(1) if body else "", re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 2:
            continue
        lab = _txt(tds[0]).rstrip("+").strip()
        if lab and lab not in out:
            out[lab] = {k: _num(_txt(v)) for k, v in zip(keys, tds[1:])}
    return out


def parse_screener(html):
    """Pure parser (no network) so it can be tested on a saved page. Returns a dict or None."""
    q = scr_table(html, "quarters")
    sales, npf = q.get("Sales"), q.get("Net Profit")
    if not sales or not npf:
        return None
    dates = sorted(d for d in sales if sales.get(d) is not None and npf.get(d) is not None and re.match(r"\d{4}-\d\d-\d\d$", d))
    if not dates:
        return None
    ratios = {}
    for li in re.findall(r'<li class="flex flex-space-between"[^>]*>(.*?)</li>', html, re.S):
        nm = re.search(r'<span class="name">(.*?)</span>', li, re.S)
        if nm:
            ratios[_txt(nm.group(1))] = [_num(_txt(v)) for v in re.findall(r'<span class="number">(.*?)</span>', li, re.S)]
    bs = scr_table(html, "balance-sheet")
    bdates = sorted(d for d in (bs.get("Equity Capital") or {}) if re.match(r"\d{4}-\d\d-\d\d$", d))
    eq = debt = None
    if bdates:
        d = bdates[-1]
        ec, rs, bo = (bs.get("Equity Capital") or {}).get(d), (bs.get("Reserves") or {}).get(d), (bs.get("Borrowings") or {}).get(d)
        eq = (ec or 0) + rs if rs is not None else None
        debt = bo
    nm = re.search(r"<h1[^>]*>.*?<span[^>]*>([^<]+)</span>\s*</h1>", html, re.S)
    return {"q": q, "dates": dates, "ratios": ratios, "equity": eq, "debt": debt, "name": _txt(nm.group(1)) if nm else ""}


def scr_row(sym, rdate, P):
    """Turn the parsed Screener page into one pead.csv row (same columns/units as build())."""
    q, ds = P["q"], P["dates"]
    cur = ds[-1]
    cd = dt.date.fromisoformat(cur)
    gap = lambda d: (cd - dt.date.fromisoformat(d)).days
    prev = next((d for d in reversed(ds[:-1]) if 60 <= gap(d) <= 125), None)
    yago = next((d for d in reversed(ds[:-1]) if abs(gap(d) - 365) <= 45), None)
    if prev is None or yago is None:
        raise Skip("Screener: previous or year-ago quarter missing")
    g = lambda lab, d: (q.get(lab) or {}).get(d)
    sales, npf, opp, eps = [g("Sales", d) for d in (cur, prev, yago)], [g("Net Profit", d) for d in (cur, prev, yago)], [g("Operating Profit", d) for d in (cur, prev, yago)], [g("EPS in Rs", d) for d in (cur, prev, yago)]
    if None in sales or None in npf:
        raise Skip("Screener: sales / net profit missing")
    last4 = ds[-4:]
    eps4 = [g("EPS in Rs", d) for d in last4]
    np4 = [g("Net Profit", d) for d in last4]
    r = P["ratios"]
    first = lambda k: (r.get(k) or [None])[0]
    hl = r.get("High / Low") or []
    f = lambda x: "" if x is None else round(x, 2)
    return {"ticker": "NSE:" + sym, "name": P["name"] or sym, "price": first("Current Price") or "", "mcap": first("Market Cap") or "", "pe": first("Stock P/E") or "",
            "high52": hl[0] if hl else "", "result_date": rdate.strftime("%d/%m/%Y") if rdate else "", "quarter_end": cur,
            "rev_cur": f(sales[0]), "rev_prev": f(sales[1]), "rev_yoy": f(sales[2]), "np_cur": f(npf[0]), "np_prev": f(npf[1]), "np_yoy": f(npf[2]),
            "ebitda_cur": f(opp[0]), "ebitda_prev": f(opp[1]), "ebitda_yoy": f(opp[2]), "eps_cur": eps[0] if eps[0] is not None else "", "eps_prev": eps[1] if eps[1] is not None else "", "eps_yoy": eps[2] if eps[2] is not None else "",
            "eps_ttm": round(sum(eps4), 2) if len(eps4) == 4 and None not in eps4 else "", "np_ttm": round(sum(np4), 2) if len(np4) == 4 and None not in np4 else "",
            "equity": f(P["equity"]), "debt": f(P["debt"]), "bvps": first("Book Value") or "", "earn_ratio": "", "vol_ratio": "", "above_ema200": "",
            "feed_note": "data from Screener.in (Yahoo had no newer quarter)"}


def hist_fields(sym, rdate):
    """volume ratio / result-day volume surge / above 200-EMA from Yahoo price history (blank if unavailable)."""
    out = {"earn_ratio": "", "vol_ratio": "", "above_ema200": ""}
    try:
        hist = yf.Ticker(sym + ".NS").history(period="2y", auto_adjust=False)
        if len(hist) > 30:
            v, c = hist["Volume"], hist["Close"]
            avg = v.tail(21).iloc[:-1].mean()
            out["vol_ratio"] = round(float(v.iloc[-1] / avg), 2) if avg else ""
            if len(c) >= 200:
                out["above_ema200"] = int(c.iloc[-1] > c.ewm(span=200, adjust=False).mean().iloc[-1])
            if rdate:
                after = hist[hist.index.date > rdate]
                if len(after):
                    i = hist.index.get_loc(after.index[0])
                    base = v.iloc[max(0, i - 20):i].mean()
                    out["earn_ratio"] = round(float(v.iloc[i] / base), 2) if base else ""
    except Exception:
        pass
    return out


def screener_build(sym, rdate):
    if SCR["off"] or SCR["n"] >= SCR_MAX:
        raise Skip("Screener fallback not used (disabled or request cap reached)")
    P = None
    for path in ("/consolidated/", "/"):
        SCR["n"] += 1
        time.sleep(1.2)
        try:
            r = requests.get(f"https://www.screener.in/company/{sym}{path}", headers=SCR_HEAD, timeout=30)
        except Exception as e:
            raise Skip(f"Screener unreachable: {type(e).__name__}")
        if r.status_code == 429 or r.status_code == 403:
            SCR["fail429"] += 1
            if SCR["fail429"] >= 3:
                SCR["off"] = True
                print("Screener is refusing requests (HTTP %s); fallback switched off for this run" % r.status_code, file=sys.stderr)
            time.sleep(10)
            raise Skip(f"Screener HTTP {r.status_code}")
        if r.status_code != 200:
            continue
        P = parse_screener(r.text)
        if P:
            break
    if not P:
        raise Skip("Screener: no quarterly table found")
    row = scr_row(sym, rdate, P)
    row.update(hist_fields(sym, rdate))
    return row


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


def build(sym, rdate, cap_check=False):
    t = yf.Ticker(sym + ".NS")
    if cap_check:
        try:
            mc = t.fast_info["market_cap"]
            if mc and mc / CR > MCAP_MAX_CR:
                raise Big(f"market cap {mc / CR:,.0f} Cr is above {MCAP_MAX_CR:,.0f} Cr")
        except Big:
            raise
        except Exception:
            pass   # cannot tell: carry on and let the normal path decide
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
    j = next((i for i in range(1, len(cols)) if abs(gap(i) - 365) <= 45), None)
    if j is None:
        raise Skip(f"year-ago quarter missing (Yahoo gave {len(cols)} quarters: " + ", ".join(c.date().isoformat() for c in cols) + ")")

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
        uni = list(dict.fromkeys(x.strip().upper().replace("NSE:", "") for x in open("tickers.txt") if x.strip() and not x.startswith("#")))
    cal = worker_results()
    for k, v in cal.items():
        if (today - v).days <= RECENT_DAYS and (k not in recent or v > recent[k]):
            recent[k] = v   # fresh filers: scanned first and given a real announcement date
    mine = set(uni) | set(recent)                    # your own list + fresh filers: never skipped by market cap
    full_list = nse_universe()
    state = load_state()
    syms = list(dict.fromkeys(list(uni) + list(recent) + full_list))
    fast = os.environ.get("FAST") == "1"   # quick runs: only stocks that filed in the last 2 days, new ones, or behind the calendar quarter
    print(f"Universe {len(syms)} symbols (your list {len(uni)}, fresh filers {len(recent)}, NSE list {len(full_list)})")
    old = {}
    if os.path.exists("pead.csv"):
        for r in csv.DictReader(open("pead.csv", encoding="utf-8")):
            qd = pd.to_datetime(r.get("quarter_end"), errors="coerce")
            if not pd.isna(qd) and (today - qd.date()).days <= QTR_MAX_AGE:
                old[r["ticker"]] = r
    if fast:
        keep = []
        for s in syms:
            o, fd = old.get("NSE:" + s), recent.get(s)
            if (o is None and s in mine) or (o is not None and (o.get("quarter_end") or "") < expected.isoformat()) or (fd and (today - fd).days <= 2):
                keep.append(s)
        print(f"FAST run: {len(keep)} of {len(syms)} symbols")
        syms = keep
    else:
        # full run: your list and fresh filers first, then everything else, least recently checked first
        def due(s):
            st = state.get(s)
            if not st or s in mine:
                return True
            if cal.get(s):
                o = old.get("NSE:" + s)
                behind = st["r"] != "ok" or (o is not None and (o.get("quarter_end") or "") < expected.isoformat())
                if behind and (cal[s] >= dt.date.fromisoformat(st["d"]) or (today - cal[s]).days <= 14):
                    return True   # announced results since we last looked, or lately and our data is still the old quarter (Yahoo / Screener can lag)
            return (today - dt.date.fromisoformat(st["d"])).days >= RECHECK.get(st["r"], 7)
        syms = [s for s in syms if due(s)]
        syms.sort(key=lambda s: (0 if s in mine else 1, (state.get(s) or {}).get("d", "")))
        print(f"Full run: {len(syms)} symbols due (rest checked recently)")
    t0 = time.time()
    new, behind, skipped, big, scanned = 0, [], [], 0, 0
    for s in syms:
        if time.time() - t0 > BUDGET_MIN * 60:
            print(f"Time budget of {BUDGET_MIN:.0f} min reached after {scanned} symbols; the next run continues with the rest")
            break
        scanned += 1
        key = "NSE:" + s
        try:
            rd = recent.get(s)
            fresh = s in mine or (cal.get(s) and (today - cal[s]).days <= 30)   # reported lately (or yours): worth asking Screener when Yahoo lags
            try:
                r = build(s, rd, cap_check=(MCAP_MAX_CR > 0 and s not in mine))
                if fresh and r["quarter_end"] < expected.isoformat():
                    try:
                        r2 = screener_build(s, rd)
                        if r2["quarter_end"] > r["quarter_end"]:
                            r = r2
                    except Skip:
                        pass
            except Skip as e:
                if not fresh:
                    raise
                try:
                    r = screener_build(s, rd)
                except Skip as e2:
                    raise Skip(f"{e} | {e2}")
            if not r["result_date"]:
                fd = nse_filing_for(s, r["quarter_end"])
                if fd:
                    r["result_date"] = fd.strftime("%d/%m/%Y")
            if not r["result_date"]:
                o = old.get(key)
                prev = valid_rd(o.get("result_date"), r["quarter_end"]) if o and o.get("quarter_end") == r["quarter_end"] else None
                if prev:
                    r["result_date"] = prev.strftime("%d/%m/%Y")
                elif o and (o.get("quarter_end") or "") < r["quarter_end"]:
                    r["result_date"] = today.strftime("%d/%m/%Y")   # a new quarter appeared since the last run: first seen today
                    r["feed_note"] = "; ".join(x for x in (r["feed_note"], "result date = first seen") if x)
            if dt.date.fromisoformat(r["quarter_end"]) < expected:
                note = f"newest quarter {r['quarter_end']} is behind calendar quarter {expected}"
                r["feed_note"] = "; ".join(x for x in (r["feed_note"], note) if x)
                behind.append(f"{s} ({r['quarter_end']})")
            old[key] = r
            state[s] = {"d": today.isoformat(), "r": "ok"}
            new += 1
            print(f"OK    {s}: quarter {r['quarter_end']}" + (f"  [{r['feed_note']}]" if r["feed_note"] else ""))
        except Big as e:
            state[s] = {"d": today.isoformat(), "r": "big"}
            old.pop(key, None)
            big += 1
            time.sleep(0.15)
            continue   # no log line: thousands of large caps would drown the log
        except Skip as e:
            print(f"SKIP  {s}: {e}")
            skipped.append(s)
            state[s] = {"d": today.isoformat(), "r": "stale" if "is older than" in str(e) else "nodata"}
            if key in old:
                old[key]["feed_note"] = f"stale, not refreshed: {e}"
        except Exception as e:
            print(f"ERROR {s}: {type(e).__name__}: {e}", file=sys.stderr)
            skipped.append(s)
            if key in old:
                old[key]["feed_note"] = f"stale, not refreshed: {type(e).__name__}"
        time.sleep(0.4)
    json.dump(state, open("scan_state.json", "w"), separators=(",", ":"))
    if SCR["n"]:
        print(f"Screener fallback: {SCR['n']} page requests" + (" (switched off after repeated refusals)" if SCR["off"] else ""))
    print(f"Scanned {scanned}: {new} scored, {big} above {MCAP_MAX_CR:,.0f} Cr, {len(skipped)} skipped (no usable Yahoo data)")
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
