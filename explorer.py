import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

PAL = ["#3B8FE0", "#F59A3D", "#E5648A", "#2EAF94", "#8B6FD6", "#5C7FA3", "#E0B52E"]
WD = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def gauge(value, title, lo, hi, good_high=True, suffix="%"):
    a, b = (lo + (hi - lo) * .35, lo + (hi - lo) * .7)
    cols = ["#FAC8DA", "#FFD3A3", "#BDEBDD"] if good_high else ["#BDEBDD", "#FFD3A3", "#FAC8DA"]
    fig = go.Figure(go.Indicator(mode="gauge+number", value=float(value), number=dict(suffix=suffix, font=dict(size=34, color="#0F2742")),
                                 title=dict(text=title, font=dict(size=15, color="#34506E")),
                                 gauge=dict(axis=dict(range=[lo, hi]), bar=dict(color="#1F5FA8", thickness=.28), bgcolor="white", borderwidth=0,
                                            steps=[dict(range=[lo, a], color=cols[0]), dict(range=[a, b], color=cols[1]), dict(range=[b, hi], color=cols[2])])))
    fig.update_layout(height=230, margin=dict(l=20, r=20, t=50, b=10)); return fig

def _card(fig, key, h=340):
    fig.update_layout(height=h)
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch", key=key)

def render(B):
    f = B["fact_full"]; months = [str(m) for m in sorted(f["month"].unique())]
    st.markdown("### Filters")
    c = st.columns([2, 1, 1, 1])
    lo, hi = c[0].select_slider("Period", options=months, value=(months[0], months[-1]), key="ex_p")
    ch = c[1].multiselect("Channel", sorted(f["sales_channel"].dropna().unique()), key="ex_c")
    gv = c[2].multiselect("Governorate", sorted(f["governorate_ar"].dropna().unique()), key="ex_g")
    ct = c[3].multiselect("Category", sorted(f["category_en"].dropna().unique()), key="ex_k")
    x = f[(f["month"].astype(str) >= lo) & (f["month"].astype(str) <= hi)]
    for col, sel in [("sales_channel", ch), ("governorate_ar", gv), ("category_en", ct)]:
        if sel: x = x[x[col].isin(sel)]
    if x.empty: st.warning("No data for this selection."); return
    rev, orders, units = x["net_line_EGP"].sum(), x["sales_order_id"].nunique(), x["quantity"].sum()
    k = st.columns(6)
    k[0].metric("Revenue", f"{rev / 1e6:,.1f}M"); k[1].metric("Orders", f"{orders:,}"); k[2].metric("Units", f"{units:,.0f}")
    k[3].metric("Avg order value", f"{rev / orders:,.0f}"); k[4].metric("Gross margin", f"{100 * x['margin_EGP'].sum() / rev:.1f}%")
    k[5].metric("Discount rate", f"{100 * x['discount_line_EGP'].sum() / x['gross_line_EGP'].sum():.1f}%")
    t1, t2, t3, t4 = st.tabs(["📈 Trends", "🧩 Mix", "🧵 Products", "🗺️ Geography"])
    m = x.groupby("month").agg(rev=("net_line_EGP", "sum"), orders=("sales_order_id", "nunique"), units=("quantity", "sum"), mar=("margin_EGP", "sum"), d=("discount_line_EGP", "sum"), g=("gross_line_EGP", "sum"))
    ix = m.index.to_timestamp()
    with t1:
        a, b = st.columns(2)
        with a:
            fig = make_subplots(specs=[[{"secondary_y": True}]]); fig.add_scatter(x=ix, y=m["rev"] / 1e6, name="Revenue (M)", fill="tozeroy", line=dict(color=PAL[0], width=3))
            fig.add_scatter(x=ix, y=m["orders"], name="Orders", line=dict(color=PAL[1], width=2), secondary_y=True); fig.update_layout(title="Revenue and orders"); _card(fig, "e1")
        with b:
            fig = go.Figure([go.Scatter(x=ix, y=100 * m["mar"] / m["rev"], name="Gross margin %", line=dict(color=PAL[3], width=3)), go.Scatter(x=ix, y=100 * m["d"] / m["g"], name="Discount %", line=dict(color=PAL[2], width=3))]); fig.update_layout(title="Margin and discount rate"); _card(fig, "e2")
        a, b = st.columns(2)
        with a:
            fig = px.line(x=ix, y=m["rev"] / m["units"], labels={"x": "", "y": "EGP"}, color_discrete_sequence=[PAL[4]]); fig.update_layout(title="Average price per unit"); _card(fig, "e3")
        with b:
            w = x.groupby(x["order_date"].dt.day_name())["net_line_EGP"].sum().reindex(WD) / 1e6
            fig = px.bar(w, labels={"value": "M EGP", "order_date": ""}, color_discrete_sequence=[PAL[5]]); fig.update_layout(title="Revenue by weekday", showlegend=False); _card(fig, "e4")
    with t2:
        a, b = st.columns(2)
        with a:
            g = x.groupby("sales_channel")["net_line_EGP"].sum(); fig = px.pie(names=g.index, values=g.values, hole=.5, color_discrete_sequence=PAL); fig.update_layout(title="Revenue by channel"); _card(fig, "e5")
        with b:
            g = x.groupby(["category_en", "product_family"])["net_line_EGP"].sum().reset_index(); fig = px.treemap(g, path=["category_en", "product_family"], values="net_line_EGP", color_discrete_sequence=PAL); fig.update_layout(title="Category and product family"); _card(fig, "e6")
        a, b = st.columns(2)
        with a:
            g = x.groupby(["sales_channel", "category_en"])["net_line_EGP"].sum().reset_index(); fig = px.sunburst(g, path=["sales_channel", "category_en"], values="net_line_EGP", color_discrete_sequence=PAL); fig.update_layout(title="Channel to category"); _card(fig, "e7")
        with b:
            g = x.groupby(["category_en", "sales_channel"])["net_line_EGP"].sum().reset_index(); fig = px.bar(g, x="category_en", y="net_line_EGP", color="sales_channel", labels={"net_line_EGP": "Revenue", "category_en": ""}); fig.update_layout(title="Category by channel"); _card(fig, "e8")
    with t3:
        a, b = st.columns(2)
        pf = x.groupby("product_family").agg(rev=("net_line_EGP", "sum"), units=("quantity", "sum"), mar=("margin_EGP", "sum")).sort_values("rev", ascending=False)
        with a:
            fig = px.bar(pf.head(15).iloc[::-1], x="rev", y=pf.head(15).index[::-1], orientation="h", labels={"rev": "Revenue (EGP)", "y": ""}, color_discrete_sequence=[PAL[0]]); fig.update_layout(title="Top 15 product families"); _card(fig, "e9", 460)
        with b:
            cum = 100 * pf["rev"].cumsum() / pf["rev"].sum(); fig = px.line(x=range(1, len(cum) + 1), y=cum.values, labels={"x": "Families (best first)", "y": "Cumulative %"}); fig.add_hline(y=80, line_dash="dash"); fig.update_layout(title="Pareto of product families"); _card(fig, "e10", 460)
        a, b = st.columns(2)
        with a:
            fig = px.scatter(pf, x="units", y="rev", size="mar", hover_name=pf.index, labels={"units": "Units", "rev": "Revenue"}, color_discrete_sequence=[PAL[2]]); fig.update_layout(title="Volume vs revenue (size = gross profit)"); _card(fig, "e11")
        with b:
            s = x.groupby("size")["quantity"].sum().sort_values(ascending=False); fig = px.bar(s, labels={"value": "Units", "size": "Size"}, color_discrete_sequence=[PAL[4]]); fig.update_layout(title="Units by size", showlegend=False); _card(fig, "e12")
    with t4:
        a, b = st.columns(2)
        with a:
            g = x.groupby("governorate_ar")["net_line_EGP"].sum().nlargest(12).iloc[::-1] / 1e6; fig = px.bar(g, orientation="h", labels={"value": "M EGP", "governorate_ar": ""}, color_discrete_sequence=[PAL[1]]); fig.update_layout(title="Top governorates", showlegend=False); _card(fig, "e13", 420)
        with b:
            g = x.groupby("branch_name_ar")["net_line_EGP"].sum().nlargest(12).iloc[::-1] / 1e6; fig = px.bar(g, orientation="h", labels={"value": "M EGP", "branch_name_ar": ""}, color_discrete_sequence=[PAL[3]]); fig.update_layout(title="Top branches", showlegend=False); _card(fig, "e14", 420)
        a, b = st.columns(2)
        with a:
            top = x.groupby("governorate_ar")["net_line_EGP"].sum().nlargest(8).index; g = x[x["governorate_ar"].isin(top)].groupby(["governorate_ar", "sales_channel"])["net_line_EGP"].sum().reset_index()
            fig = px.bar(g, x="governorate_ar", y="net_line_EGP", color="sales_channel", labels={"net_line_EGP": "Revenue", "governorate_ar": ""}); fig.update_layout(title="Governorate by channel"); _card(fig, "e15")
        with b:
            g = x.groupby("branch_id")["net_line_EGP"].sum() / 1e6; fig = px.histogram(g, nbins=20, labels={"value": "Branch revenue (M EGP)", "count": "Branches"}, color_discrete_sequence=[PAL[4]]); fig.update_layout(title="Branch revenue distribution", showlegend=False); _card(fig, "e16")
