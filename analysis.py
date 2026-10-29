"""All calculations (sections 3-12 of the notebook). Every function takes the bundle B and is cached inside it."""
import numpy as np
import pandas as pd
from config import EXCLUDE_OPEX_MARKETING, RECENT_MONTHS

def cached(fn):
    def w(B, *a):
        k = (fn.__name__,) + a
        if k not in B["_c"]:
            B["_c"][k] = fn(B, *a)
        return B["_c"][k]
    return w

def share(B, by, top=10):
    t = B["fact_full"].groupby(by)["net_line_EGP"].sum().sort_values(ascending=False)
    return pd.DataFrame({"revenue": t, "share_%": 100 * t / t.sum()}).head(top)

@cached
def pnl(B):
    d, f = B["data"], B["fact"]
    mo = lambda df, c, v: df.groupby(df[c].dt.to_period("M"))[v].sum()
    ox = d["operating_expenses"]
    ox = ox[ox["expense_category"] != "Marketing"] if EXCLUDE_OPEX_MARKETING else ox
    pr = d["payroll"]; pr = pr.groupby(pd.PeriodIndex(pr["pay_month"].astype(str), freq="M"))["net_paid_EGP"].sum()
    c = d["marketing_campaigns"].copy()
    c["days"] = ((c["end_date"] - c["start_date"]).dt.days + 1).clip(lower=1)
    e = c.loc[c.index.repeat(c["days"])].copy()
    e["date"] = e["start_date"] + pd.to_timedelta(e.groupby("campaign_id").cumcount(), unit="D")
    mk = (e["spend_EGP"] / e["days"]).groupby(e["date"].dt.to_period("M")).sum()
    p = pd.concat({"revenue": f.groupby("month")["net_line_EGP"].sum(), "cogs": f.groupby("month")["cogs_EGP"].sum(),
                   "returns": mo(d["sales_returns"], "return_date", "refund_amount_EGP"), "opex": mo(ox, "expense_date", "amount_EGP"),
                   "payroll": pr, "transfer": mo(d["inventory_transfers"], "transfer_date", "transport_cost_EGP"),
                   "marketing": mk}, axis=1).fillna(0)
    p = p[p.index.isin(B["full_months"])].sort_index()
    p["gross"] = p["revenue"] - p["cogs"]
    p["net"] = p["gross"] - p[["returns", "opex", "payroll", "transfer", "marketing"]].sum(axis=1)
    return p

@cached
def yearly(B):
    p = pnl(B); y = p.groupby(p.index.year).sum()
    y.insert(0, "months", p.groupby(p.index.year).size())
    y["marketing_%"] = 100 * y["marketing"] / y["revenue"]
    y["gross_margin_%"] = 100 * y["gross"] / y["revenue"]
    return y

@cached
def monthly(B):
    m = B["fact_full"].groupby("month").agg(revenue=("net_line_EGP", "sum"), units=("quantity", "sum"), orders=("sales_order_id", "nunique"))
    m["price_per_unit"] = m["revenue"] / m["units"]
    return m

@cached
def campaigns(B):
    c = B["data"]["marketing_campaigns"].copy()
    c["cpc"] = c["spend_EGP"] / c["clicks"]; c["ctr_%"] = 100 * c["clicks"] / c["impressions"]
    o = B["orders"].merge(B["data"]["branches"][["branch_id", "governorate_ar"]], on="branch_id", how="left")
    d = o.groupby(["order_date", "governorate_ar"]).size().unstack(fill_value=0)
    d = d.reindex(pd.date_range(d.index.min(), d.index.max()), fill_value=0)
    cs = pd.concat([pd.DataFrame(0, index=[d.index[0] - pd.Timedelta(days=1)], columns=d.columns), d.cumsum()])
    def real(r):
        g = r["governorate_ar"]
        if g not in cs.columns: return np.nan
        s, e = max(r["start_date"], d.index[0]), min(r["end_date"], d.index[-1])
        return 0 if e < s else cs.loc[e, g] - cs.loc[s - pd.Timedelta(days=1), g]
    c["real_orders"] = c.apply(real, axis=1)
    return c

@cached
def channels(B):
    c = campaigns(B)
    t = c.groupby("channel").agg(spend=("spend_EGP", "sum"), impressions=("impressions", "sum"), clicks=("clicks", "sum"), attributed=("orders_attributed", "sum"))
    t["cpc"] = t["spend"] / t["clicks"]; t["ctr_%"] = 100 * t["clicks"] / t["impressions"]; t["spend_share_%"] = 100 * t["spend"] / t["spend"].sum()
    return t.sort_values("cpc")

@cached
def disc_buckets(B):
    f = B["fact_full"][["gross_line_EGP", "discount_line_EGP", "margin_EGP", "net_line_EGP", "quantity"]].copy()
    f["rate"] = (f["discount_line_EGP"] / f["gross_line_EGP"].replace(0, np.nan)).fillna(0)
    f["bucket"] = pd.cut(f["rate"], [-1e-9, 0, .05, .10, .15, .20, .30, 1.0], labels=["0%", "0-5%", "5-10%", "10-15%", "15-20%", "20-30%", ">30%"])
    g = f.groupby("bucket", observed=True).agg(lines=("rate", "size"), units=("quantity", "sum"), margin=("margin_EGP", "sum"), net=("net_line_EGP", "sum"), disc=("discount_line_EGP", "sum"))
    g["margin_%"] = 100 * g["margin"] / g["net"]; g["avg_qty"] = g["units"] / g["lines"]
    d, m = f["discount_line_EGP"].sum() / f["gross_line_EGP"].sum(), (f["margin_EGP"] + f["discount_line_EGP"]).sum() / f["gross_line_EGP"].sum()
    return dict(table=g, rate=100 * d, breakeven=100 * d / (m - d) if m > d else np.nan, lines_disc=100 * (f["rate"] > 0).mean(), lost_profit=100 * f["discount_line_EGP"].sum() / (f["margin_EGP"] + f["discount_line_EGP"]).sum())

@cached
def stock(B):
    ms = B["data"]["monthly_stock"].copy(); ms["month"] = pd.PeriodIndex(ms["year_month"].astype(str), freq="M")
    f = B["fact"]
    sold = f.groupby(["month", "branch_id", "category_en"])["quantity"].sum().rename("sold").reset_index().rename(columns={"branch_id": "stock_location_id", "category_en": "product_category"})
    br = ms[ms["stock_location_type"] == "Branch"].merge(sold, on=["month", "stock_location_id", "product_category"], how="left")
    br = br[br["month"].isin(B["full_months"])].copy(); br["sold"] = br["sold"].fillna(0)
    br["cover"] = br["closing_units"] / br["sold"].replace(0, np.nan)
    br["bucket"] = pd.cut(br["cover"], [0, .5, 1, 3, 6, np.inf], labels=["<0.5", "0.5-1", "1-3", "3-6", ">6 months"])
    b = br.groupby("bucket", observed=True).agg(value=("closing_stock_value_EGP", "sum"), risk=("stockout_risk_score", "mean"))
    tot = br["closing_stock_value_EGP"].sum()   # all branch stock, including rows with no sales (cover undefined)
    b["share_%"] = 100 * b["value"] / tot
    dead = 100 * br.loc[(br["sold"] == 0) & (br["closing_units"] > 0), "closing_stock_value_EGP"].sum() / tot
    last = ms["month"].max()
    lt = ms[ms["month"] == last].groupby("product_category").agg(units=("closing_units", "sum"), value=("closing_stock_value_EGP", "sum"))
    lt["monthly_sold"] = f[f["month"].isin(B["full_months"][-3:])].groupby("category_en")["quantity"].sum() / 3
    lt["cover"] = lt["units"] / lt["monthly_sold"]
    return dict(buckets=b, dead=dead, latest=lt.sort_values("cover", ascending=False), corr=br["stockout_risk_score"].corr(br["cover"], method="spearman"), last=str(last))

@cached
def purchasing(B):
    d, f = B["data"], B["fact"]
    b = d["purchase_order_items"].groupby("sku_id").agg(bought=("quantity", "sum"), cost=("line_cost_EGP", "sum"))
    s = f.groupby("sku_id").agg(sold=("quantity", "sum"), cogs=("cogs_EGP", "sum"))
    sk = b.join(s, how="outer").fillna(0).join(d["sku_variants"].set_index("sku_id")["product_id"])
    p = sk.groupby("product_id")[["bought", "sold", "cost", "cogs"]].sum()
    return dict(p=p, corr=p["bought"].corr(p["sold"]), cost_x=p["cost"].sum() / p["cogs"].sum(), units_x=p["bought"].sum() / p["sold"].sum())

@cached
def returns(B):
    r, f = B["data"]["sales_returns"], B["fact"]
    m = r.merge(f[["sales_line_id", "category_en"]], on="sales_line_id", how="left")
    cat = (100 * m.groupby("category_en")["return_quantity"].sum() / f.groupby("category_en")["quantity"].sum()).sort_values(ascending=False)
    rs = r.groupby("reason").agg(count=("return_id", "count"), refund=("refund_amount_EGP", "sum"))
    return dict(cat=cat, reasons=rs, rate=100 * r["return_quantity"].sum() / f["quantity"].sum(), refund=r["refund_amount_EGP"].sum())

@cached
def decline(B, by):
    mm = monthly(B); n = RECENT_MONTHS
    pe = mm.index.get_loc(mm["revenue"].rolling(n).sum().idxmax())
    peak, rec = list(mm.index[pe - n + 1: pe + 1]), list(mm.index[-n:])
    f = B["fact_full"]
    t = pd.concat([f[f["month"].isin(peak)].groupby(by)["net_line_EGP"].sum().rename("peak"), f[f["month"].isin(rec)].groupby(by)["net_line_EGP"].sum().rename("recent")], axis=1).fillna(0)
    t["change"] = t["recent"] - t["peak"]
    return t.sort_values("change"), peak, rec

@cached
def summary(B):
    y, p, mm, c, d = yearly(B), pnl(B), monthly(B), campaigns(B), disc_buckets(B)
    fy = y[y["months"] == 12]; L = fy.iloc[-1]; n = min(12, len(mm) // 2)
    g = mm.iloc[-n:].mean() / mm.iloc[:n].mean()
    pu, st = purchasing(B), stock(B)
    return dict(last_year=int(fy.index[-1]), revenue=L["revenue"], net=L["net"], marketing_pct=L["marketing_%"], gross_margin=100 * p["gross"].sum() / p["revenue"].sum(),
                loss_months=int((p["net"] < 0).sum()), months=len(p), revenue_x=g["revenue"], orders_x=g["orders"], price_x=g["price_per_unit"],
                attributed_x=c["orders_attributed"].sum() / len(B["orders"]), discount_pct=d["rate"], breakeven=d["breakeven"], purchases_x=pu["cost_x"], buy_sell_corr=pu["corr"],
                over6=st["buckets"]["share_%"].get(">6 months", np.nan), risk_corr=st["corr"], return_rate=returns(B)["rate"])
