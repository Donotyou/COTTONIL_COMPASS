"""Questions & answers: each question computes a live answer (text) and a chart from the data."""
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import analysis as A

Q = []
def q(group, title):
    def deco(fn):
        Q.append(dict(id=f"q{len(Q) + 1}", group=group, title=title, fn=fn)); return fn
    return deco

PAL = ["#3B8FE0", "#F59A3D", "#E5648A", "#2EAF94", "#8B6FD6", "#5C7FA3", "#E0B52E"]
M = lambda v: f"{v / 1e6:,.1f}M"

@q("Profit & Loss", "Is the company profitable, and since when?")
def _(B):
    y, p = A.yearly(B), A.pnl(B)
    fig = go.Figure([go.Bar(x=y.index.astype(str), y=y["net"] / 1e6, name="Net profit (M EGP)", marker_color=["#8FD3C1" if v >= 0 else "#F2A6B8" for v in y["net"]])])
    fig.add_scatter(x=y.index.astype(str), y=y["revenue"] / 1e6, name="Revenue (M EGP)", mode="lines+markers", line=dict(color="#7DB9F0"))
    pos = y[y["net"] > 0]
    return (f"{int((p['net'] < 0).sum())} of {len(p)} full months were loss-making. " +
            (f"The first profitable year was {pos.index[0]} (net {M(pos['net'].iloc[0])})." if len(pos) else "No year was profitable yet.") +
            " Net profit is an estimate (imports and shipping costs are not included).", fig)

@q("Profit & Loss", "How much of revenue does marketing consume over time?")
def _(B):
    y = A.yearly(B)
    fig = px.line(y, x=y.index.astype(str), y="marketing_%", markers=True, labels={"x": "Year", "marketing_%": "Marketing % of revenue"})
    return f"Marketing was {y['marketing_%'].iloc[1]:.0f}% of revenue in {y.index[1]} and {y['marketing_%'].iloc[-2]:.0f}% in {y.index[-2]}: spend stays roughly flat in EGP while revenue grows.", fig

@q("Profit & Loss", "Is growth coming from volume or from price?")
def _(B):
    m = A.monthly(B); n = min(12, len(m) // 2); idx = (m[["revenue", "orders", "units", "price_per_unit"]] / m[["revenue", "orders", "units", "price_per_unit"]].iloc[:n].mean() * 100)
    fig = px.line(idx, x=idx.index.to_timestamp(), y=idx.columns, labels={"value": "Index (first 12 months = 100)", "x": "", "variable": ""}); fig.update_yaxes(type="log")
    s = A.summary(B)
    return f"Revenue grew {s['revenue_x']:.1f}x but orders only {s['orders_x']:.1f}x; price per unit grew {s['price_x']:.1f}x. Most growth is price-driven (compare with inflation before judging).", fig

@q("Marketing", "Which platform has the cheapest cost per click?")
def _(B):
    c = A.channels(B)
    fig = px.bar(c, x=c.index, y="cpc", labels={"cpc": "Cost per click (EGP)", "x": ""}, color_discrete_sequence=["#7DB9F0"])
    return f"{c.index[0]} is cheapest ({c['cpc'].iloc[0]:.2f} EGP) and {c.index[-1]} the most expensive ({c['cpc'].iloc[-1]:.2f}). Platforms are close; the big spread is between campaigns inside each platform.", fig

@q("Marketing", "Are the attributed orders real?")
def _(B):
    c = A.campaigns(B); real = len(B["orders"]); att = c["orders_attributed"].sum()
    fig = px.bar(x=["Attributed by campaigns", "Actual orders in sales"], y=[att, real], color_discrete_sequence=["#F6B26B"], labels={"x": "", "y": "Orders"})
    r2 = c["clicks"].corr(c["orders_attributed"]) ** 2
    return f"Campaigns claim {att / real:.1f}x more orders than the company actually received. Attributed orders track clicks (R² {r2:.2f}), not real sales, so they should not be used to judge ROI.", fig

@q("Marketing", "Does spending more in a month bring more sales?")
def _(B):
    p = A.pnl(B); ch = p[["marketing", "revenue"]].pct_change().replace([np.inf, -np.inf], np.nan)
    fig = px.scatter(ch, x="marketing", y="revenue", labels={"marketing": "Change in marketing spend", "revenue": "Change in revenue"}, color_discrete_sequence=["#7DB9F0"])
    return f"Correlation between monthly changes in spend and revenue is {ch['marketing'].corr(ch['revenue']):.2f}. Near zero means no visible effect of spend on sales.", fig

@q("Discounts", "Do deeper discounts bring bigger quantities?")
def _(B):
    d = A.disc_buckets(B); t = d["table"]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=t.index.astype(str), y=t["margin_%"], name="Margin %", marker_color="#7DB9F0")
    fig.add_scatter(x=t.index.astype(str), y=t["avg_qty"], name="Avg qty per line", mode="lines+markers", line=dict(color="#F6B26B"), secondary_y=True)
    fig.update_yaxes(rangemode="tozero", secondary_y=True)
    return f"Discounts are {d['rate']:.1f}% of gross sales on {d['lines_disc']:.0f}% of lines and remove {d['lost_profit']:.1f}% of potential profit. A discount must lift volume by {d['breakeven']:.1f}% to break even, yet average quantity barely changes with depth.", fig

@q("Sales & Concentration", "Where is revenue concentrated?")
def _(B):
    c = A.share(B, "category_en", 10)
    fig = px.bar(c[::-1], x="share_%", y=c.index[::-1], orientation="h", labels={"share_%": "% of revenue", "y": ""}, color_discrete_sequence=["#8FD3C1"])
    ch, g = A.share(B, "sales_channel", 5), A.share(B, "governorate_ar", 1)
    return f"Top 3 categories = {c['share_%'].head(3).sum():.0f}% of revenue. {ch.index[0]} brings {ch['share_%'].iloc[0]:.0f}%; the top governorate ({g.index[0]}) brings {g['share_%'].iloc[0]:.0f}%.", fig

@q("Sales & Concentration", "Why did revenue fall from its peak?")
def _(B):
    t, peak, rec = A.decline(B, "sales_channel"); top = A.decline(B, "category_en")[0].head(2)
    fig = px.bar(t, x=t.index, y="change", labels={"change": "Revenue change (EGP)", "x": ""}, color_discrete_sequence=["#F2A6B8"])
    return f"Comparing {rec[0]}-{rec[-1]} with the best window ({peak[0]}-{peak[-1]}): revenue moved {t['change'].sum() / 1e6:,.1f}M. Biggest category drops: {', '.join(top.index)}.", fig

@q("Inventory & Purchasing", "Which categories hold the most idle stock?")
def _(B):
    s = A.stock(B); t = s["latest"]
    fig = px.bar(t[::-1], x="cover", y=t.index[::-1], orientation="h", labels={"cover": "Months of cover (log)", "y": ""}, color_discrete_sequence=["#B9A7F0"]); fig.update_xaxes(type="log")
    return f"Latest stock ({s['last']}) covers {t['cover'].median():.0f} months of sales for the median category; {s['buckets']['share_%'].get('>6 months', 0):.0f}% of branch stock value covers more than 6 months.", fig

@q("Inventory & Purchasing", "Does purchasing follow demand?")
def _(B):
    p = A.purchasing(B); t = p["p"]
    fig = px.scatter(t, x="sold", y="bought", log_x=True, log_y=True, labels={"sold": "Units sold", "bought": "Units purchased"}, color_discrete_sequence=["#7DB9F0"])
    return f"Purchases vs sales correlation by product: {p['corr']:.2f}. Purchase cost is {p['cost_x']:.1f}x the cost of goods sold. A ratio this far from 1 usually means the purchase table is on a different scale: verify it before acting.", fig

@q("Inventory & Purchasing", "Can we trust the stock-out risk score?")
def _(B):
    s = A.stock(B); b = s["buckets"]
    fig = px.bar(b, x=b.index.astype(str), y="risk", labels={"risk": "Average stock-out risk", "x": "Months of cover"}, color_discrete_sequence=["#F9D58B"]); fig.update_yaxes(range=[0, 1])
    return f"Correlation between the score and real cover is {s['corr']:.2f}. The score is flat across cover buckets, so it does not reflect real shortage risk.", fig

@q("Returns & Delivery", "What drives returns?")
def _(B):
    r = A.returns(B); rs = r["reasons"]
    fig = px.bar(rs, x=rs.index, y="count", labels={"count": "Returns", "x": ""}, color_discrete_sequence=["#F2A6B8"])
    return f"Return rate is {r['rate']:.2f}% of units ({M(r['refund'])} refunded). Reasons are spread almost evenly, so the reason coding adds little insight; highest-rate category: {r['cat'].index[0]} ({r['cat'].iloc[0]:.2f}%).", fig


def _pf(B): return B["fact_full"]
_t = lambda idx: idx.to_timestamp()

@q("Profit & Loss", "Did monthly profit improve over time?")
def _(B):
    p = A.pnl(B); r = p["net"].rolling(12).mean(); l12 = p["net"].tail(12)
    fig = go.Figure([go.Bar(x=_t(p.index), y=p["net"] / 1e6, name="Monthly net (M EGP)", marker_color=np.where(p["net"] >= 0, "#2EAF94", "#E5648A"))])
    fig.add_scatter(x=_t(p.index), y=r / 1e6, name="12-month average", line=dict(color="#1F3A5F", width=3))
    return f"{int((l12 > 0).sum())} of the last 12 months were profitable (average {M(l12.mean())} per month).\n\n**So what:** the trend, not a single month, shows whether the turnaround is real. Watch the dark average line stay above zero.", fig

@q("Profit & Loss", "Where does each EGP of revenue go?")
def _(B):
    y = A.yearly(B); y = y[y["months"] == 12]; L, yr = y.iloc[-1], y.index[-1]
    v = {"Cost of goods": L.cogs, "Marketing": L.marketing, "Operating expenses": L.opex, "Payroll": L.payroll, "Returns": L.returns, "Stock transfers": L.transfer, "Net profit": max(L.net, 0)}
    fig = px.pie(names=list(v), values=list(v.values()), hole=.45)
    return f"In {yr}, cost of goods takes {100 * L.cogs / L.revenue:.0f}% of revenue, marketing {100 * L.marketing / L.revenue:.0f}%, operating expenses {100 * L.opex / L.revenue:.0f}%, payroll {100 * L.payroll / L.revenue:.0f}%; profit keeps {100 * max(L.net, 0) / L.revenue:.0f}%.\n\n**So what:** the largest controllable slices after cost of goods are marketing and operating expenses.", fig

@q("Profit & Loss", "Is gross margin stable?")
def _(B):
    p = A.pnl(B); gm = 100 * p["gross"] / p["revenue"]
    fig = px.line(x=_t(p.index), y=gm, labels={"x": "", "y": "Gross margin %"}); fig.update_yaxes(range=[0, max(60, gm.max() + 5)])
    return f"Gross margin ranges {gm.min():.1f}%-{gm.max():.1f}% (average {gm.mean():.1f}%).\n\n**So what:** a flat line means product pricing and cost are stable; losses come from costs below gross profit, not from the products.", fig

@q("Profit & Loss", "Is payroll complete in recent months?")
def _(B):
    p = A.pnl(B)
    fig = px.bar(x=_t(p.index), y=p["payroll"] / 1e6, labels={"x": "", "y": "Payroll (M EGP)"}, color_discrete_sequence=["#8B6FD6"])
    a, b = p["payroll"].tail(9).mean(), p["payroll"].iloc[-21:-9].mean()
    return f"Average monthly payroll: {M(a)} in the last 9 months vs {M(b)} in the 12 months before.\n\n**So what:** a sharp drop usually means missing records, not savings. Profit for the latest year is overstated until this is checked.", fig

@q("Profit & Loss", "Which calendar months are strongest? (seasonality)")
def _(B):
    m = A.monthly(B)["revenue"]; d = pd.DataFrame({"y": m.index.year, "m": m.index.month, "v": m.values})
    pv = d.pivot(index="y", columns="m", values="v"); pv = pv.div(pv.mean(axis=1), axis=0)
    fig = px.imshow(pv, color_continuous_scale="Blues", aspect="auto", labels=dict(x="Month", y="Year", color="vs year avg"))
    return f"Strongest month on average: {int(pv.mean().idxmax())}; weakest: {int(pv.mean().idxmin())}.\n\n**So what:** plan stock, staffing and campaigns around the dark cells instead of spreading them evenly.", fig

@q("Marketing", "How uneven is campaign cost inside each platform?")
def _(B):
    c = A.campaigns(B); g = c.groupby("channel")["cpc"].quantile([.1, .9]).unstack()
    fig = px.box(c, x="channel", y="cpc", log_y=True, labels={"cpc": "Cost per click (log)", "channel": ""})
    return f"Within one platform the p90 campaign costs {(g[0.9] / g[0.1]).median():.1f}x more per click than the p10 campaign.\n\n**So what:** pick winners campaign by campaign, not platform by platform; cap or stop the high-CPC campaigns.", fig

@q("Marketing", "Does marketing spend follow real demand by governorate?")
def _(B):
    c = A.campaigns(B); o = B["orders"].merge(B["data"]["branches"][["branch_id", "governorate_ar"]], on="branch_id")
    df = pd.DataFrame({"spend": c.groupby("governorate_ar")["spend_EGP"].sum() / 1e6, "orders": o.groupby("governorate_ar").size()}).dropna()
    fig = px.scatter(df, x="orders", y="spend", text=df.index, labels={"orders": "Actual orders", "spend": "Marketing spend (M EGP)"}); fig.update_traces(textposition="top center")
    return f"Correlation between governorate spend and actual orders: {df['spend'].corr(df['orders']):.2f}.\n\n**So what:** points far above the trend are over-funded relative to demand; test cutting spend there first.", fig

@q("Marketing", "Do marketing and revenue move together month by month?")
def _(B):
    p = A.pnl(B); fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_scatter(x=_t(p.index), y=p["revenue"] / 1e6, name="Revenue (M)", line=dict(color="#3B8FE0", width=3))
    fig.add_scatter(x=_t(p.index), y=p["marketing"] / 1e6, name="Marketing (M)", line=dict(color="#F59A3D", width=3), secondary_y=True)
    return f"Marketing is about {p['marketing'].tail(12).mean() / 1e6:.1f}M per month while revenue rose to {p['revenue'].iloc[-1] / 1e6:.1f}M.\n\n**So what:** spend that stays flat while revenue grows 10x suggests revenue growth is not driven by marketing.", fig

@q("Discounts", "Which categories get the deepest discounts?")
def _(B):
    f = _pf(B); g = (100 * f.groupby("category_en")["discount_line_EGP"].sum() / f.groupby("category_en")["gross_line_EGP"].sum()).sort_values()
    fig = px.bar(g, orientation="h", labels={"value": "Discount % of gross", "category_en": ""}, color_discrete_sequence=["#F59A3D"]); fig.update_layout(showlegend=False)
    return f"Deepest: {g.index[-1]} ({g.iloc[-1]:.1f}%); shallowest: {g.index[0]} ({g.iloc[0]:.1f}%).\n\n**So what:** if every category discounts about the same, discounts follow habit, not strategy. Target them at slow-moving categories.", fig

@q("Discounts", "Is discounting rising over time?")
def _(B):
    f = _pf(B).groupby("month").agg(d=("discount_line_EGP", "sum"), g=("gross_line_EGP", "sum")); r = 100 * f["d"] / f["g"]
    fig = px.line(x=_t(r.index), y=r, labels={"x": "", "y": "Discount % of gross"}); fig.update_yaxes(rangemode="tozero")
    return f"Discount rate moved between {r.min():.1f}% and {r.max():.1f}% (latest {r.iloc[-1]:.1f}%).\n\n**So what:** a rising line means growth is being bought; a flat line means discounts are a fixed habit.", fig

@q("Sales & Concentration", "How concentrated are products? (Pareto)")
def _(B):
    s = _pf(B).groupby("product_family")["net_line_EGP"].sum().sort_values(ascending=False); cum = 100 * s.cumsum() / s.sum()
    fig = px.line(x=range(1, len(s) + 1), y=cum.values, labels={"x": "Product families (best first)", "y": "Cumulative % of revenue"}); fig.add_hline(y=80, line_dash="dash")
    return f"{int((cum < 80).sum() + 1)} of {len(s)} product families make 80% of revenue.\n\n**So what:** the long tail adds complexity and stock; review which tail products deserve their shelf space.", fig

@q("Sales & Concentration", "Retail vs wholesale vs e-commerce: who matters?")
def _(B):
    g = B["orders"].groupby("sales_channel").agg(orders=("sales_order_id", "count"), rev=("net_before_tax_EGP", "sum"))
    d = pd.DataFrame({"Share of orders %": 100 * g["orders"] / g["orders"].sum(), "Share of revenue %": 100 * g["rev"] / g["rev"].sum()})
    fig = px.bar(d, barmode="group", labels={"value": "%", "sales_channel": ""}); aov = (g["rev"] / g["orders"]).round(0)
    return "Average order value (EGP): " + ", ".join(f"{k} {v:,.0f}" for k, v in aov.items()) + ".\n\n**So what:** a channel with few orders but large revenue (wholesale) needs account management, not mass marketing.", fig

@q("Sales & Concentration", "Which governorates sell the most?")
def _(B):
    g = A.share(B, "governorate_ar", 10)
    fig = px.bar(g, y="share_%", labels={"share_%": "% of revenue", "governorate_ar": ""}, color_discrete_sequence=["#3B8FE0"])
    return f"{g.index[0]} brings {g['share_%'].iloc[0]:.0f}% and the top 3 bring {g['share_%'].head(3).sum():.0f}% (by branch location).\n\n**So what:** dependence on a few governorates is a risk and also shows where expansion is still untested.", fig

@q("Sales & Concentration", "Which categories earn the best margin?")
def _(B):
    f = _pf(B).groupby("category_en").agg(m=("margin_EGP", "sum"), n=("net_line_EGP", "sum")); r = (100 * f["m"] / f["n"]).sort_values()
    fig = px.bar(r, orientation="h", labels={"value": "Gross margin %", "category_en": ""}, color_discrete_sequence=["#2EAF94"]); fig.update_layout(showlegend=False)
    return f"Margins range {r.iloc[0]:.1f}%-{r.iloc[-1]:.1f}%.\n\n**So what:** near-identical margins mean pricing is uniform; look for categories where a price test could lift margin.", fig

@q("Customers & Branches", "How loyal are registered customers?")
def _(B):
    o = B["orders"]; n = o[o["customer_id"] != "GUEST"].groupby("customer_id").size(); vc = n.clip(upper=15).value_counts().sort_index()
    fig = px.bar(x=vc.index, y=vc.values, labels={"x": "Orders per customer (15 = 15+)", "y": "Customers"}, color_discrete_sequence=["#8B6FD6"])
    return f"{100 * (n >= 2).mean():.0f}% of registered customers ordered more than once (average {n.mean():.1f} orders).\n\n**So what:** very high repeat rates are unusual for retail; check how customer ids are assigned before building loyalty plans.", fig

@q("Customers & Branches", "Who are the customers? (segment and age)")
def _(B):
    o = B["orders"].merge(B["data"]["customers"][["customer_id", "customer_segment", "age_band"]], on="customer_id", how="left")
    g = o.dropna(subset=["customer_segment"]).groupby(["age_band", "customer_segment"])["net_before_tax_EGP"].sum().reset_index()
    fig = px.bar(g, x="age_band", y="net_before_tax_EGP", color="customer_segment", labels={"net_before_tax_EGP": "Revenue (EGP)", "age_band": "Age band"})
    guest = o.loc[o["customer_id"] == "GUEST", "net_before_tax_EGP"].sum() / o["net_before_tax_EGP"].sum() * 100
    return f"{guest:.0f}% of revenue comes from orders with no customer record.\n\n**So what:** that revenue cannot be targeted or retained; capture phone/email at checkout.", fig

@q("Customers & Branches", "Which branches are weakest?")
def _(B):
    f = _pf(B).groupby(["branch_id", "branch_name_ar"])["net_line_EGP"].sum().reset_index()
    f = f.merge(B["data"]["branches"][["branch_id", "opening_date"]], on="branch_id"); f["months"] = ((B["fact"]["order_date"].max() - f["opening_date"]).dt.days / 30.4).clip(lower=1)
    f["per_month"] = f["net_line_EGP"] / f["months"]; w = f.sort_values("per_month").head(10)
    fig = px.bar(w, x="per_month", y="branch_name_ar", orientation="h", labels={"per_month": "Revenue per month open (EGP)", "branch_name_ar": ""}, color_discrete_sequence=["#E5648A"])
    return f"The 10 weakest branches generate {100 * w['net_line_EGP'].sum() / f['net_line_EGP'].sum():.1f}% of revenue.\n\n**So what:** review these for relocation, format change or closure, after checking their rent in operating expenses.", fig

@q("Inventory & Purchasing", "How much money is tied up in stock, by category?")
def _(B):
    s = A.stock(B); t = s["latest"].sort_values("value")
    fig = px.bar(t, x="value", y=t.index, orientation="h", labels={"value": f"Stock value {s['last']} (EGP)", "product_category": ""}, color_discrete_sequence=["#5C7FA3"])
    return f"Total stock value in the latest month: {M(t['value'].sum())}; the largest category is {t.index[-1]} ({M(t['value'].iloc[-1])}).\n\n**So what:** compare against months of cover: high value plus high cover is the first place to stop purchasing.", fig

@q("Inventory & Purchasing", "Bought vs sold units by category")
def _(B):
    p = A.purchasing(B)["p"].join(B["data"]["products_catalog"].set_index("product_id")["category_en"]).groupby("category_en")[["bought", "sold"]].sum()
    fig = px.bar(p, barmode="group", log_y=True, labels={"value": "Units (log)", "category_en": ""})
    return f"Overall purchases are {p['bought'].sum() / p['sold'].sum():.1f}x units sold.\n\n**So what:** if purchases dwarf sales in every category, either the purchase table has a different scale or buying is not demand-based. Verify first.", fig

@q("Returns & Delivery", "Which categories are returned most?")
def _(B):
    c = A.returns(B)["cat"]
    fig = px.bar(c[::-1], orientation="h", labels={"value": "Returned % of units sold", "category_en": ""}, color_discrete_sequence=["#E5648A"]); fig.update_layout(showlegend=False)
    return f"Highest: {c.index[0]} ({c.iloc[0]:.2f}%); lowest: {c.index[-1]} ({c.iloc[-1]:.2f}%).\n\n**So what:** returns are low overall; focus on a category only if its rate is far above the others.", fig

@q("Returns & Delivery", "Which carrier delivers faster and more reliably?")
def _(B):
    d = B["data"]["delivery_shipments"].copy(); d["late"] = d["fulfillment_status"].eq("Delayed") * 100; d["days"] = (d["delivery_date"] - d["ship_date"]).dt.days
    g = d.groupby("carrier").agg(late=("late", "mean"), days=("days", "mean"), n=("late", "size"))
    fig = px.bar(g, y="late", labels={"late": "Delayed shipments %", "carrier": ""}, color_discrete_sequence=["#F59A3D"])
    return "Average delivery days: " + ", ".join(f"{k} {v:.1f}" for k, v in g["days"].items()) + f". Overall {d['late'].mean():.1f}% delayed.\n\n**So what:** shift volume to the carrier with fewer delays only if the fee is similar.", fig


_wd = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
def _fy(B):
    y = A.yearly(B); return y[y["months"] == 12]

@q("Profit & Loss", "How does revenue turn into profit? (waterfall)")
def _(B):
    L = _fy(B).iloc[-1]; st_ = [("Revenue", L.revenue), ("Cost of goods", -L.cogs), ("Returns", -L.returns), ("Operating exp.", -L.opex), ("Payroll", -L.payroll), ("Transfers", -L.transfer), ("Marketing", -L.marketing)]
    fig = go.Figure(go.Waterfall(x=[a for a, _ in st_] + ["Net profit"], y=[b / 1e6 for _, b in st_] + [0], measure=["absolute"] + ["relative"] * 6 + ["total"], connector=dict(line=dict(color="#BFD3E8")))); fig.update_yaxes(title="M EGP")
    return f"Last full year: revenue {M(L.revenue)} leaves {M(L.net)} after all costs.\n\n**So what:** every red step is a lever; compare their size against the profit that remains.", fig

@q("Profit & Loss", "How much profit has the company accumulated?")
def _(B):
    c = A.pnl(B)["net"].cumsum(); fig = px.area(x=_t(c.index), y=c / 1e6, labels={"x": "", "y": "Cumulative net (M EGP)"}, color_discrete_sequence=["#3B8FE0"])
    return f"Cumulative net profit stands at {M(c.iloc[-1])}; the lowest point was {M(c.min())}.\n\n**So what:** the curve shows how long recovery takes after the deepest point; a rising tail confirms the turnaround.", fig

@q("Profit & Loss", "How does each year compare month by month?")
def _(B):
    m = A.monthly(B)["revenue"]; d = pd.DataFrame({"Year": m.index.year.astype(str), "Month": m.index.month, "Revenue": m.values / 1e6})
    fig = px.line(d, x="Month", y="Revenue", color="Year", markers=True, labels={"Revenue": "Revenue (M EGP)"}); fig.update_xaxes(dtick=1)
    return "Each line is a year; lines that sit higher and keep the same shape show growth with stable seasonality.\n\n**So what:** use the shape of the best months to schedule stock and campaigns.", fig

@q("Profit & Loss", "Is the average order value rising?")
def _(B):
    m = A.monthly(B); aov = m["revenue"] / m["orders"]
    fig = px.line(x=_t(m.index), y=aov, labels={"x": "", "y": "Average order value (EGP)"}, color_discrete_sequence=["#F59A3D"])
    return f"Average order value moved from {aov.iloc[:12].mean():,.0f} to {aov.iloc[-12:].mean():,.0f} EGP (first vs last 12 months).\n\n**So what:** a rising value with flat order counts means growth from price or mix, not from more customers.", fig

@q("Profit & Loss", "Which operating expenses are largest?")
def _(B):
    e = B["data"]["operating_expenses"].groupby("expense_category")["amount_EGP"].sum().sort_values()
    fig = px.bar(e / 1e6, orientation="h", labels={"value": "M EGP", "expense_category": ""}, color_discrete_sequence=["#5C7FA3"]); fig.update_layout(showlegend=False)
    return f"Largest: {e.index[-1]} ({M(e.iloc[-1])}), then {e.index[-2]} ({M(e.iloc[-2])}).\n\n**So what:** fixed items such as rent and utilities are renegotiation targets; check why they are so much bigger than the rest.", fig

@q("Profit & Loss", "Does gross profit cover fixed costs every month?")
def _(B):
    p = A.pnl(B); fixed = p[["opex", "payroll", "marketing", "transfer", "returns"]].sum(axis=1)
    fig = go.Figure([go.Scatter(x=_t(p.index), y=p["gross"] / 1e6, name="Gross profit", line=dict(color="#2EAF94", width=3)), go.Scatter(x=_t(p.index), y=fixed / 1e6, name="Operating costs", line=dict(color="#E5648A", width=3))]); fig.update_yaxes(title="M EGP")
    return f"Gross profit covered operating costs in {int((p['gross'] > fixed).sum())} of {len(p)} months.\n\n**So what:** where the pink line is above the green one, costs exceed what products earn; that gap is the monthly break-even target.", fig

@q("Marketing", "Which campaigns are expensive but unproductive? (bubble)")
def _(B):
    c = A.campaigns(B)
    fig = px.scatter(c, x="ctr_%", y="cpc", size="spend_EGP", color="channel", log_y=True, labels={"ctr_%": "Click-through rate %", "cpc": "Cost per click (log)"})
    return "Campaigns in the top-left (low click rate, high cost) waste the most; big bubbles are where the money goes.\n\n**So what:** review the large top-left bubbles first; they combine high spend with poor traffic quality.", fig

@q("Marketing", "How did spend per platform change by year?")
def _(B):
    c = A.campaigns(B).assign(year=lambda d: d["start_date"].dt.year.astype(str)); g = c.groupby(["year", "channel"])["spend_EGP"].sum().reset_index()
    fig = px.bar(g, x="year", y="spend_EGP", color="channel", labels={"spend_EGP": "Spend (EGP)", "year": ""})
    return "Stacked bars show which platforms receive the budget each year.\n\n**So what:** if shares are almost identical every year, budgets are allocated by habit, not by performance.", fig

@q("Marketing", "From impressions to real orders: where does the funnel break?")
def _(B):
    c = A.campaigns(B); v = [c["impressions"].sum(), c["clicks"].sum(), c["orders_attributed"].sum(), len(B["orders"])]
    fig = px.bar(x=v, y=["Impressions", "Clicks", "Attributed orders", "Actual orders (all channels)"], orientation="h", log_x=True, labels={"x": "Count (log)", "y": ""}, color_discrete_sequence=["#8B6FD6"])
    return f"Clicks are {100 * v[1] / v[0]:.1f}% of impressions; attributed orders {100 * v[2] / v[1]:.1f}% of clicks, yet actual orders are {v[3] / v[2]:.1%} of attributed.\n\n**So what:** the last step proves attribution is overstated; measure conversion with real tracking.", fig

@q("Marketing", "Are campaigns spending their budget?")
def _(B):
    c = A.campaigns(B); u = 100 * c["spend_EGP"] / c["budget_EGP"]
    fig = px.histogram(u, nbins=30, labels={"value": "Spend as % of budget", "count": "Campaigns"}, color_discrete_sequence=["#F59A3D"]); fig.update_layout(showlegend=False)
    return f"Campaigns spend {u.median():.0f}% of budget on median; {int((u > 100).sum())} exceed it.\n\n**So what:** unspent budget is an easy saving; overspent campaigns need approval rules.", fig

@q("Marketing", "Which 10 campaigns cost the most per click?")
def _(B):
    c = A.campaigns(B); t = c[c["spend_EGP"] > c["spend_EGP"].median()].nlargest(10, "cpc")
    fig = px.bar(t, x="cpc", y="campaign_id", orientation="h", color="channel", labels={"cpc": "Cost per click (EGP)", "campaign_id": ""})
    return f"These 10 (among above-median spenders) cost {t['cpc'].mean():.2f} EGP per click vs {c['cpc'].median():.2f} median.\n\n**So what:** pausing or re-targeting them is the quickest test of marketing efficiency.", fig

@q("Discounts", "Where are discounts deepest? (category x channel)")
def _(B):
    f = _pf(B).groupby(["category_en", "sales_channel"]).agg(d=("discount_line_EGP", "sum"), g=("gross_line_EGP", "sum")); r = (100 * f["d"] / f["g"]).unstack()
    fig = px.imshow(r, color_continuous_scale="Oranges", aspect="auto", labels=dict(color="Discount %"), text_auto=".1f")
    return f"Discount rates range {r.min().min():.1f}%-{r.max().max():.1f}% across the grid.\n\n**So what:** a flat grid means no policy differentiates categories or channels; set explicit rules per cell.", fig

@q("Discounts", "How is discount spend split across years and channels?")
def _(B):
    f = _pf(B).groupby(["year", "sales_channel"])["discount_line_EGP"].sum().reset_index(); f["year"] = f["year"].astype(str)
    fig = px.bar(f, x="year", y="discount_line_EGP", color="sales_channel", barmode="group", labels={"discount_line_EGP": "Discount (EGP)", "year": ""})
    return "Discount spend grows with revenue; check whether it grows faster in any channel.\n\n**So what:** channels where discounts grow faster than sales should lose discount autonomy first.", fig

@q("Discounts", "How much profit do discounts remove each year?")
def _(B):
    f = _pf(B).groupby("year").agg(d=("discount_line_EGP", "sum"), m=("margin_EGP", "sum")); pot = 100 * f["d"] / (f["d"] + f["m"])
    fig = make_subplots(specs=[[{"secondary_y": True}]]); fig.add_bar(x=f.index.astype(str), y=f["d"] / 1e6, name="Discount (M EGP)", marker_color="#F59A3D")
    fig.add_scatter(x=f.index.astype(str), y=pot, name="% of potential profit", line=dict(color="#E5648A", width=3), secondary_y=True)
    return f"Discounts removed {pot.iloc[-1]:.1f}% of potential profit in {f.index[-1]}.\n\n**So what:** this is the profit you give up for volume that the data does not show.", fig

@q("Sales & Concentration", "What is the product hierarchy? (treemap)")
def _(B):
    d = _pf(B).groupby(["category_en", "product_family"])["net_line_EGP"].sum().reset_index()
    fig = px.treemap(d, path=["category_en", "product_family"], values="net_line_EGP", color_discrete_sequence=PAL)
    return "Box size is revenue; click a category to drill into its product families.\n\n**So what:** a few big boxes carry the business; many small boxes are complexity.", fig

@q("Sales & Concentration", "How do channels and categories combine? (sunburst)")
def _(B):
    d = _pf(B).groupby(["sales_channel", "category_en"])["net_line_EGP"].sum().reset_index()
    fig = px.sunburst(d, path=["sales_channel", "category_en"], values="net_line_EGP", color_discrete_sequence=PAL)
    return "Inner ring: channel; outer ring: category within that channel.\n\n**So what:** a category that dominates one channel may be invisible in another: a cross-sell opportunity.", fig

@q("Sales & Concentration", "Which weekday sells the most?")
def _(B):
    f = _pf(B); g = f.groupby(f["order_date"].dt.day_name())["net_line_EGP"].sum().reindex(_wd)
    fig = px.bar(g / 1e6, labels={"value": "Revenue (M EGP)", "order_date": ""}, color_discrete_sequence=["#3B8FE0"]); fig.update_layout(showlegend=False)
    return f"Best day: {g.idxmax()} ({100 * g.max() / g.sum():.0f}% of revenue); weakest: {g.idxmin()}.\n\n**So what:** schedule staff, promotions and shipping around the strongest days.", fig

@q("Sales & Concentration", "Which sizes sell the most?")
def _(B):
    g = _pf(B).groupby("size")["quantity"].sum().sort_values(ascending=False)
    fig = px.bar(g, labels={"value": "Units sold", "size": "Size"}, color_discrete_sequence=["#8B6FD6"]); fig.update_layout(showlegend=False)
    return f"{g.index[0]} leads with {100 * g.iloc[0] / g.sum():.0f}% of units.\n\n**So what:** align purchasing size curves with this mix; fewer slow sizes means less idle stock.", fig

@q("Sales & Concentration", "Which governorates buy through which channel?")
def _(B):
    f = _pf(B); top = f.groupby("governorate_ar")["net_line_EGP"].sum().nlargest(8).index
    d = f[f["governorate_ar"].isin(top)].groupby(["governorate_ar", "sales_channel"])["net_line_EGP"].sum().reset_index()
    fig = px.bar(d, x="governorate_ar", y="net_line_EGP", color="sales_channel", labels={"net_line_EGP": "Revenue (EGP)", "governorate_ar": ""})
    return "Channel mix differs by region.\n\n**So what:** regions with little wholesale or e-commerce are growth gaps worth testing.", fig

@q("Sales & Concentration", "Which categories are big, profitable or both? (bubble)")
def _(B):
    d = _pf(B).groupby("category_en").agg(units=("quantity", "sum"), rev=("net_line_EGP", "sum"), m=("margin_EGP", "sum")).reset_index()
    fig = px.scatter(d, x="units", y="rev", size="m", text="category_en", labels={"units": "Units sold", "rev": "Revenue (EGP)"}); fig.update_traces(textposition="top center")
    return "Position shows volume vs revenue; bubble size is total gross profit.\n\n**So what:** big units but low revenue means low price per unit; compare with the bubble size to see if it still pays.", fig

@q("Sales & Concentration", "Which categories grew or shrank last year?")
def _(B):
    y = _fy(B).index[-2:]
    if len(y) < 2: return "Needs two full years of data.", go.Figure()
    f = _pf(B); g = f[f["year"].isin(y)].groupby(["category_en", "year"])["net_line_EGP"].sum().unstack(); gr = (100 * (g[y[1]] / g[y[0]] - 1)).sort_values()
    fig = px.bar(gr, orientation="h", labels={"value": f"Growth {y[0]}-{y[1]} %", "category_en": ""}, color_discrete_sequence=["#2EAF94"]); fig.update_layout(showlegend=False)
    return f"Fastest: {gr.index[-1]} ({gr.iloc[-1]:+.0f}%); slowest: {gr.index[0]} ({gr.iloc[0]:+.0f}%).\n\n**So what:** compare with overall price growth; categories below it are shrinking in real terms.", fig

@q("Customers & Branches", "Which branches sell the most?")
def _(B):
    g = _pf(B).groupby("branch_name_ar")["net_line_EGP"].sum().nlargest(10).sort_values()
    fig = px.bar(g / 1e6, orientation="h", labels={"value": "Revenue (M EGP)", "branch_name_ar": ""}, color_discrete_sequence=["#3B8FE0"]); fig.update_layout(showlegend=False)
    return f"The top 10 branches make {100 * g.sum() / _pf(B)['net_line_EGP'].sum():.0f}% of revenue.\n\n**So what:** study what the best branches do (location, stock, staff) and copy it.", fig

@q("Customers & Branches", "How is revenue spread across branches?")
def _(B):
    g = _pf(B).groupby("branch_id")["net_line_EGP"].sum() / 1e6
    fig = px.histogram(g, nbins=20, labels={"value": "Branch revenue (M EGP)", "count": "Branches"}, color_discrete_sequence=["#8B6FD6"]); fig.update_layout(showlegend=False)
    return f"Branch revenue ranges {g.min():.1f}M-{g.max():.1f}M (median {g.median():.1f}M).\n\n**So what:** a wide spread means branch format or location matters; a narrow one means the network is homogeneous.", fig

@q("Customers & Branches", "Does branch age explain revenue?")
def _(B):
    f = _pf(B).groupby(["branch_id", "branch_name_ar"])["net_line_EGP"].sum().reset_index().merge(B["data"]["branches"][["branch_id", "opening_date"]], on="branch_id")
    f["age"] = (B["fact"]["order_date"].max() - f["opening_date"]).dt.days / 365; f["rev"] = f["net_line_EGP"] / 1e6
    fig = px.scatter(f, x="age", y="rev", hover_name="branch_name_ar", labels={"age": "Branch age (years)", "rev": "Revenue (M EGP)"}, color_discrete_sequence=["#E5648A"])
    return f"Correlation between age and revenue: {f['age'].corr(f['rev']):.2f}.\n\n**So what:** a weak link means young branches can match old ones, so ramp-up time is not the issue.", fig

@q("Customers & Branches", "How many customers joined each year?")
def _(B):
    c = B["data"]["customers"]; g = c.groupby(c["joined_date"].dt.year).size()
    fig = px.bar(x=g.index.astype(str), y=g.values, labels={"x": "Year", "y": "New customers"}, color_discrete_sequence=["#2EAF94"])
    return f"{len(c):,} customers in the base; peak year {int(g.idxmax())} ({g.max():,}).\n\n**So what:** compare acquisition with marketing spend per year to see the cost per new customer.", fig

@q("Inventory & Purchasing", "Value vs cover per category: where is money stuck? (bubble)")
def _(B):
    t = A.stock(B)["latest"].reset_index()
    fig = px.scatter(t, x="cover", y="value", size="value", text="product_category", log_x=True, labels={"cover": "Months of cover (log)", "value": "Stock value (EGP)"}); fig.update_traces(textposition="top center")
    return "Right = more months of cover; higher = more money. Big bubbles top-right are the priority.\n\n**So what:** stop purchasing there and clear stock with targeted offers.", fig

@q("Inventory & Purchasing", "How is the stock-out risk score distributed?")
def _(B):
    r = B["data"]["monthly_stock"]["stockout_risk_score"]
    fig = px.histogram(r, nbins=30, labels={"value": "Stock-out risk score", "count": "Rows"}, color_discrete_sequence=["#F59A3D"]); fig.update_layout(showlegend=False)
    return f"{100 * (r > 0.5).mean():.0f}% of rows score above 0.5.\n\n**So what:** only use the score for decisions after it is validated against real cover.", fig

@q("Inventory & Purchasing", "Which suppliers receive the most purchase value?")
def _(B):
    d = B["data"]; p = d["purchase_order_items"].merge(d["purchase_orders"][["po_id", "supplier_id", "po_status"]], on="po_id").groupby("supplier_id")["line_cost_EGP"].sum().nlargest(10).sort_values()
    fig = px.bar(p / 1e6, orientation="h", labels={"value": "Purchase cost (M EGP)", "supplier_id": ""}, color_discrete_sequence=["#5C7FA3"]); fig.update_layout(showlegend=False)
    return f"Top supplier {p.index[-1]} receives {100 * p.iloc[-1] / p.sum():.0f}% of the top-10 spend.\n\n**So what:** concentration gives negotiating power but also supply risk.", fig

@q("Inventory & Purchasing", "Purchases vs cost of goods sold over time")
def _(B):
    d = B["data"]; p = d["purchase_order_items"].merge(d["purchase_orders"][["po_id", "po_date"]], on="po_id"); pm = p.groupby(p["po_date"].dt.to_period("M"))["line_cost_EGP"].sum()
    c = A.pnl(B)["cogs"]; fig = go.Figure([go.Scatter(x=_t(pm.index), y=pm.values, name="Purchases", line=dict(color="#8B6FD6", width=3)), go.Scatter(x=_t(c.index), y=c.values, name="Cost of goods sold", line=dict(color="#2EAF94", width=3))]); fig.update_yaxes(type="log", title="EGP (log)")
    return f"Purchases are {pm.sum() / c.sum():.1f}x cost of goods sold over the period.\n\n**So what:** the two lines should track each other; a constant large gap points to a data-scale problem or heavy overbuying.", fig

@q("Returns & Delivery", "Which sizes are returned most?")
def _(B):
    f = B["fact"]; r = B["data"]["sales_returns"].merge(f[["sales_line_id", "size"]], on="sales_line_id"); g = (100 * r.groupby("size")["return_quantity"].sum() / f.groupby("size")["quantity"].sum()).sort_values()
    fig = px.bar(g, labels={"value": "Returned % of units", "size": "Size"}, color_discrete_sequence=["#E5648A"]); fig.update_layout(showlegend=False)
    return f"Highest return rate: size {g.index[-1]} ({g.iloc[-1]:.2f}%).\n\n**So what:** a size with a clearly higher rate suggests a fit problem; fix the size guide before changing the product.", fig

@q("Returns & Delivery", "Which return reasons dominate in each category?")
def _(B):
    r = B["data"]["sales_returns"].merge(B["fact"][["sales_line_id", "category_en"]], on="sales_line_id"); ct = pd.crosstab(r["category_en"], r["reason"], normalize="index") * 100
    fig = px.imshow(ct, color_continuous_scale="Reds", aspect="auto", text_auto=".0f", labels=dict(color="%"))
    return "Each row sums to 100%; darker cells are the main reason within that category.\n\n**So what:** uniform rows mean reasons are not recorded reliably; require a mandatory reason at the till.", fig

@q("Returns & Delivery", "How many refunds are paid each month?")
def _(B):
    r = B["data"]["sales_returns"]; g = r.groupby(r["return_date"].dt.to_period("M"))["refund_amount_EGP"].sum()
    fig = px.area(x=_t(g.index), y=g.values / 1e6, labels={"x": "", "y": "Refunds (M EGP)"}, color_discrete_sequence=["#E5648A"])
    return f"Latest month: {M(g.iloc[-1])} refunded; average {M(g.mean())}.\n\n**So what:** refunds rise with sales; watch for months that jump faster than revenue.", fig

@q("Returns & Delivery", "How long does delivery take for each carrier?")
def _(B):
    d = B["data"]["delivery_shipments"].copy(); d["days"] = (d["delivery_date"] - d["ship_date"]).dt.days
    fig = px.histogram(d, x="days", color="carrier", barmode="overlay", opacity=.65, labels={"days": "Delivery days", "count": "Shipments"})
    return f"Median delivery time is {d['days'].median():.0f} days; the slowest 5% take {d['days'].quantile(.95):.0f}+ days.\n\n**So what:** set customer promises at the 90th percentile, not the average.", fig

@q("Returns & Delivery", "Which governorates have the most delayed shipments?")
def _(B):
    d = B["data"]["delivery_shipments"]; g = (100 * d["fulfillment_status"].eq("Delayed").groupby(d["ship_to_governorate"]).mean()).nlargest(10).sort_values()
    fig = px.bar(g, orientation="h", labels={"value": "Delayed %", "ship_to_governorate": ""}, color_discrete_sequence=["#F59A3D"]); fig.update_layout(showlegend=False)
    return f"Worst: {g.index[-1]} ({g.iloc[-1]:.1f}% delayed).\n\n**So what:** route these governorates through the more reliable carrier.", fig

def by_group(g):
    return [x for x in Q if x["group"] == g]
