import json, os
import pandas as pd
import analysis as A
import config
from config import MODEL


CHAT_MODEL = getattr(config, "CHAT_MODEL", MODEL)

def quality_alerts(B):
    out = []
    add = lambda sev, title, detail: out.append(dict(severity=sev, title=title, detail=detail))
    s, y = A.summary(B), A.yearly(B)
    if not 0.5 <= s["purchases_x"] <= 2:
        add("High", "Purchases do not match sales scale", f"Purchase cost is {s['purchases_x']:.1f}x the cost of goods sold (expected about 1-1.3x). Check units/currency/duplicated lines in purchase_order_items.")
    if len(y) >= 2:
        pm = y["payroll"] / y["months"]
        if pm.iloc[-1] < 0.6 * pm.iloc[-2]:
            add("High", f"Payroll {y.index[-1]} looks incomplete", f"Average monthly payroll fell from {pm.iloc[-2] / 1e6:.2f}M to {pm.iloc[-1] / 1e6:.2f}M, so {y.index[-1]} profit may be overstated.")
    if s["attributed_x"] > 1.5:
        add("High", "Attributed orders exceed real orders", f"Campaign table claims {s['attributed_x']:.1f}x the actual orders. Do not use it for ROI.")
    if abs(s["risk_corr"]) < 0.1:
        add("Medium", "Stock-out risk score is not informative", f"Correlation with real months of cover is {s['risk_corr']:.2f}.")
    lt = A.stock(B)["latest"]
    if lt["cover"].median() > 12:
        add("Medium", "Stock cover is extreme", f"Median category covers {lt['cover'].median():.0f} months of sales. Confirm the stock table units/scale.")
    r = A.returns(B)["reasons"]
    if len(r) > 1 and (r["count"].max() - r["count"].min()) / r["count"].sum() < 0.03:
        add("Low", "Return reasons are almost uniform", "Each reason has about the same share, so reason coding is likely not reliable.")
    g = (B["orders"]["customer_id"] == "GUEST").mean() * 100
    if g > 10:
        add("Low", "Many orders without a customer", f"{g:.0f}% of orders have no customer_id (treated as GUEST).")
    ls = B["data"]["sales_order_items"].groupby("sales_order_id")["net_line_EGP"].sum()
    o = B["orders"].set_index("sales_order_id")["net_before_tax_EGP"]
    bad = ((o - ls.reindex(o.index)).abs() > 0.05).mean() * 100
    if bad > 0.5:
        add("Medium", "Order totals differ from line totals", f"{bad:.1f}% of orders do not equal the sum of their lines.")
    add("Info", "Partial months excluded", f"Trend analyses use {len(B['full_months'])} full months ({B['full_months'][0]} to {B['full_months'][-1]}).")
    return sorted(out, key=lambda x: ["High", "Medium", "Low", "Info"].index(x["severity"]))

GROUPS = {"month": "month", "year": "year", "governorate": "governorate_ar", "category": "category_en", "channel": "sales_channel",
          "branch": "branch_name_ar", "product_family": "product_family"}
METRICS = {"revenue": ("net_line_EGP", "sum"), "units": ("quantity", "sum"), "gross_profit": ("margin_EGP", "sum"), "orders": ("sales_order_id", "nunique")}

def _n(text):
    t = str(text).strip().lower()
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        t = t.replace(a, b)
    return t

def query_sales(B, metric="revenue", group_by="none", start=None, end=None, compare_start=None, compare_end=None, **flt):
    f = B["fact"]
    if (compare_start or compare_end) and group_by in ("month", "year"): group_by = "none"   # labels would not align
    def one(s, e):
        x = f
        if s: x = x[x["order_date"] >= pd.Timestamp(s)]
        if e: x = x[x["order_date"] <= pd.Timestamp(e)]
        for k, v in flt.items():
            if v and k in GROUPS:
                nv = _n(v)
                x = x[x[GROUPS[k]].astype(str).map(_n).str.contains(nv, na=False, regex=False)]
        col, fn = METRICS[metric]
        if group_by == "none": return pd.Series({"total": x[col].agg(fn)})
        return x.groupby(GROUPS[group_by])[col].agg(fn).sort_values(ascending=False).head(40)
    a = one(start, end).rename("period_a")
    if compare_start or compare_end:
        b = one(compare_start, compare_end).rename("period_b")
        t = pd.concat([a, b], axis=1).fillna(0); t["change_%"] = 100 * (t["period_a"] / t["period_b"].replace(0, float("nan")) - 1)
    else:
        t = a.to_frame()
    t.index = t.index.astype(str); t.index.name = group_by if group_by != "none" else "metric"
    return t.reset_index()

def finance(B, view):
    v = {"yearly_pnl": lambda: A.yearly(B), "monthly_pnl": lambda: A.pnl(B).tail(12), "marketing_channels": lambda: A.channels(B),
         "discount_buckets": lambda: A.disc_buckets(B)["table"], "stock_cover": lambda: A.stock(B)["latest"],
         "returns_by_category": lambda: A.returns(B)["cat"].to_frame(), "alerts": lambda: pd.DataFrame(quality_alerts(B))}[view]()
    v = v.copy(); v.index = v.index.astype(str)
    return v.reset_index().round(2)

TOOLS = [
    {"name": "query_sales", "description": "Query sales from the tables. Revenue is net before tax in EGP. Use ISO dates (YYYY-MM-DD). Add compare_* dates to compare two periods (comparison returns totals when group_by is month/year; for a trend, omit compare_*).",
     "input_schema": {"type": "object", "properties": {
         "metric": {"type": "string", "enum": list(METRICS)}, "group_by": {"type": "string", "enum": ["none"] + list(GROUPS)},
         "start": {"type": "string"}, "end": {"type": "string"}, "compare_start": {"type": "string"}, "compare_end": {"type": "string"},
         "governorate": {"type": "string", "description": "Arabic name exactly as in the data"}, "category": {"type": "string"},
         "channel": {"type": "string"}, "branch": {"type": "string"}, "product_family": {"type": "string"}}, "required": ["metric"]}},
    {"name": "finance", "description": "Pre-computed tables: P&L, marketing, discounts, stock, returns, data-quality alerts.",
     "input_schema": {"type": "object", "properties": {"view": {"type": "string", "enum": ["yearly_pnl", "monthly_pnl", "marketing_channels", "discount_buckets", "stock_cover", "returns_by_category", "alerts"]}}, "required": ["view"]}}]

def _system(B):
    f = B["fact"]
    return ("You are a friendly business analyst chatbot for the managers of Cottonil, an Egyptian cotton apparel company. "
            "LANGUAGE RULE: reply in the same language as the user's latest message. Arabic (any dialect, incl. Egyptian) gets Arabic in the same dialect; English gets English. "
            "If the user mixes both, reply in the language of the main sentence and keep technical terms (EGP, ROI, SKU) as they are. "
            "Always get numbers by calling the tools; never invent figures. "
            "Give the number, the comparison, and one sentence of interpretation. Mention data caveats when relevant (call finance 'alerts' if unsure). "
            "Be conversational and short (3-5 lines). If a follow-up says 'it' or 'that', use the previous context. "
            "Filter values must match the data (Arabic names for governorate/branch). If the user writes them in English (e.g. Cairo), translate to the exact Arabic name from the lists below before calling the tool. "
            "If a filter returns no rows, say the name may be spelled differently and suggest the closest option from the lists below. "
            "If the question is not about Cottonil's data, say briefly that you only answer questions about the data. "
            "End with ONE relevant follow-up question the user could ask next. "
            f"Data covers {f['order_date'].min().date()} to {f['order_date'].max().date()}; 'today' means the last date in the data. Money is EGP.\n"
            f"Governorates: {', '.join(sorted(f['governorate_ar'].dropna().unique()))}\nCategories: {', '.join(sorted(f['category_en'].dropna().unique()))}\n"
            f"Channels: {', '.join(sorted(f['sales_channel'].dropna().unique()))}")

GEMINI_MODEL = getattr(config, "GEMINI_MODEL", "gemini-2.5-flash")   # if you hit rate limits try "gemini-2.5-flash-lite"

def _client(key):
    from google import genai
    return genai.Client(api_key=key or os.getenv("GEMINI_API_KEY"))

def _gemini_tools():
    from google.genai import types
    return [types.Tool(function_declarations=[
        types.FunctionDeclaration(name=t["name"], description=t["description"], parameters=t["input_schema"]) for t in TOOLS])]

def ask(B, question, history, key=None):

    from google.genai import types
    history = history[-12:]                      
    role = {"user": "user", "assistant": "model"}
    contents = [types.Content(role=role[m["role"]], parts=[types.Part(text=m["content"])]) for m in history]
    contents.append(types.Content(role="user", parts=[types.Part(text=question)]))
    used, c = [], _client(key)
    cfg = types.GenerateContentConfig(system_instruction=_system(B), tools=_gemini_tools(), max_output_tokens=2000)
    for _ in range(5):
        try:
            r = c.models.generate_content(model=GEMINI_MODEL, contents=contents, config=cfg)
        except Exception as e:
            m = str(e)
            if "429" in m or "RESOURCE_EXHAUSTED" in m:
                return "Rate limit reached, wait a minute and try again. / وصلنا للحد المجاني، استني دقيقة وجرّب تاني.", used, history
            return f"error: {m[:200]}", used, history
        calls = r.function_calls or []
        if not calls:
            ans = (r.text or "").strip()
            return ans, used, history + [{"role": "user", "content": question}, {"role": "assistant", "content": ans}]
        contents.append(r.candidates[0].content)
        parts = []
        for fc in calls:
            args = dict(fc.args or {})
            try:
                df = query_sales(B, **args) if fc.name == "query_sales" else finance(B, **args)
                used.append((f"{fc.name}: {json.dumps(args, ensure_ascii=False)}", df))
                out = df.head(25).to_json(orient="records", force_ascii=False) if len(df) else "no rows matched; check the filter values or dates"
            except Exception as e:
                out = f"error: {e}"
            parts.append(types.Part.from_function_response(name=fc.name, response={"result": out}))
        contents.append(types.Content(role="user", parts=parts))
    return "I couldn't finish the analysis, try a narrower question. / ما قدرتش أكمل التحليل، جرّب سؤال أضيق.", used, history

def weekly_facts(B):
    f = B["fact"]; end = f["order_date"].max().normalize(); d = pd.Timedelta
    P = {"this_week": (end - d(days=6), end), "previous_week": (end - d(days=13), end - d(days=7)), "same_week_last_year": (end - d(days=370), end - d(days=364))}
    rows = {}
    for k, (s, e) in P.items():
        x = f[(f["order_date"] >= s) & (f["order_date"] <= e)]
        rows[k] = dict(period=f"{s.date()} to {e.date()}", revenue=x["net_line_EGP"].sum(), orders=x["sales_order_id"].nunique(), units=x["quantity"].sum(), gross_profit=x["margin_EGP"].sum())
    tbl = pd.DataFrame(rows).T
    mv = {}
    for dim in ["sales_channel", "governorate_ar", "category_en"]:
        a = f[(f["order_date"] >= P["this_week"][0])].groupby(dim)["net_line_EGP"].sum()
        b = f[(f["order_date"] >= P["previous_week"][0]) & (f["order_date"] <= P["previous_week"][1])].groupby(dim)["net_line_EGP"].sum()
        t = pd.concat([a.rename("this"), b.rename("prev")], axis=1).fillna(0); t["change"] = t["this"] - t["prev"]
        mv[dim] = t.sort_values("change").iloc[[0, -1]].round(0).reset_index().to_dict("records")
    return dict(weeks=tbl.reset_index().rename(columns={"index": "week"}).to_dict("records"), movers=mv, alerts=quality_alerts(B), pnl_last_3_months=A.pnl(B).tail(3).round(0).reset_index().astype(str).to_dict("records"))

def weekly_report(B, key=None, lang="Arabic"):
    facts = weekly_facts(B)
    prompt = (f"Write the weekly management report in {lang} from these facts only. Structure: headline; key numbers vs previous week and vs last year (with % change); "
              "biggest movers (channel, governorate, category); latest P&L months; data alerts that affect trust; 3 recommended actions. Be concise.\n\n" + json.dumps(facts, ensure_ascii=False, default=str))
    from google.genai import types
    r = _client(key).models.generate_content(model=GEMINI_MODEL, contents=prompt, config=types.GenerateContentConfig(max_output_tokens=3000))
    return (r.text or "").strip(), facts