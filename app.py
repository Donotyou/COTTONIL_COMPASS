import os
import pandas as pd
import plotly.express as px
import streamlit as st
import data, theme, qa, ai, explorer
import analysis as A

st.set_page_config(page_title="Cottonil Compass", page_icon="🧭", layout="wide")
theme.apply()

@st.cache_resource(show_spinner="Loading and cleaning your tables…")
def get_bundle():
    return data.build(data.load())

try:
    B = get_bundle()
except Exception as e:
    st.error(f"Could not load the tables. Check TABLES_PATH in config.py (or env COTTONIL_TABLES). Details: {e}"); st.stop()

PAGES = ["Overview", "Explorer", "Profit & Loss", "Marketing", "Discounts", "Sales & Concentration", "Customers & Branches", "Inventory & Purchasing", "Returns & Delivery", "Questions & Answers", "AI Assistant"]
GROUPS = PAGES[2:9]
st.sidebar.markdown("## 🧭 Cottonil Compass")
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")
st.sidebar.caption(f"{len(B['orders']):,} orders · {len(B['full_months'])} full months")

META = {"Profit & Loss": ("💰", "Where profit is made and lost, month by month", "blue"), "Marketing": ("📣", "What marketing costs and what it really returns", "pink"),
        "Discounts": ("🏷️", "How discounts affect margin and volume", "orange"), "Sales & Concentration": ("🛍️", "Who buys what, where and through which channel", "blue"),
        "Customers & Branches": ("🏬", "Customer loyalty and branch performance", "mint"), "Inventory & Purchasing": ("📦", "Money tied up in stock and how buying follows demand", "orange"),
        "Returns & Delivery": ("🚚", "Why items come back and how reliably orders arrive", "pink")}

def run(item):
    k = ("qa", item["id"])
    if k not in B["_c"]: B["_c"][k] = item["fn"](B)
    return B["_c"][k]

def show(item, k=""):
    text, fig = run(item)[:2]
    fig.update_layout(height=380)
    with st.container(border=True):
        st.markdown(f"#### {item['title']}")
        st.plotly_chart(fig, width="stretch", key=item["id"] + page + k)
        st.markdown(text)

def grid(items):
    for i in range(0, len(items), 2):
        for c, it in zip(st.columns(2), items[i:i + 2]):
            with c: show(it)

if page == "Overview":
    s = A.summary(B); st.title("Business Health Check")
    st.caption("Everything below is computed live from your tables.")
    c = st.columns(4)
    c[0].metric(f"Revenue {s['last_year']}", f"{s['revenue'] / 1e6:,.1f}M"); c[1].metric("Gross margin", f"{s['gross_margin']:.1f}%")
    c[2].metric(f"Net profit {s['last_year']}", f"{s['net'] / 1e6:,.1f}M"); c[3].metric("Loss months", f"{s['loss_months']} / {s['months']}")
    st.markdown("### Ranked problems")
    for i, (t, d) in enumerate([
        ("Marketing without real measurement", f"Campaigns claim {s['attributed_x']:.1f}x the actual orders; marketing is {s['marketing_pct']:.1f}% of {s['last_year']} revenue."),
        ("Idle stock", f"{s['over6']:.0f}% of branch stock value covers more than 6 months of sales."),
        ("Purchasing disconnected from sales", f"Purchases are {s['purchases_x']:.0f}x cost of goods sold (correlation {s['buy_sell_corr']:.2f}). Verify the table first."),
        ("Discounts without volume effect", f"{s['discount_pct']:.1f}% of gross sales; needs +{s['breakeven']:.1f}% volume just to break even."),
        ("Growth driven by price", f"Revenue {s['revenue_x']:.1f}x vs orders {s['orders_x']:.1f}x."),
        ("Unreliable stock-out score", f"Correlation with real cover: {s['risk_corr']:.2f}.")], 1):
        st.markdown(f"**{i}. {t}**  \n{d}")
    gc = st.columns(4)
    for n, (col, fig) in enumerate(zip(gc, [explorer.gauge(s["gross_margin"], "Gross margin", 0, 60), explorer.gauge(s["marketing_pct"], f"Marketing % of revenue {s['last_year']}", 0, 60, False),
                             explorer.gauge(s["over6"], "Branch stock > 6 months of cover", 0, 100, False), explorer.gauge(s["discount_pct"], "Discount % of gross sales", 0, 15, False)])):
        with col, st.container(border=True): st.plotly_chart(fig, width="stretch", key=f"gauge{n}")
    st.markdown("### Key charts")
    grid([x for x in qa.Q if x["id"] in ("q1", "q2", "q5", "q8", "q9", "q10", "q14", "q15")])
elif page == "Explorer":
    theme.banner("Explorer", "Filter by period, channel, governorate and category: 16 linked charts update together", "🔎", "blue")
    explorer.render(B)
elif page in GROUPS:
    ic, sub, tone = META[page]; theme.banner(page, sub, ic, tone)
    its = qa.by_group(page); theme.takeaways([run(x)[0].split("\n\n")[0] for x in its[:3]])
    grid(its)
elif page == "Questions & Answers":
    theme.banner("Questions & Answers", f"{len(qa.Q)} business questions answered live from your data: every chart comes with a written reading and a decision hint", "💬", "pink")
    c1, c2 = st.columns([2, 1]); term = c1.text_input("Search questions", placeholder="e.g. discount, stock, branch, delivery…")
    topic = c2.selectbox("Topic", ["All topics"] + GROUPS)
    pool = [x for x in qa.Q if (topic == "All topics" or x["group"] == topic) and term.lower() in (x["title"] + x["group"]).lower()]
    st.caption(f"Showing {len(pool)} of {len(qa.Q)} questions" + ("" if term or topic != "All topics" else " (choose a topic or search to narrow down)"))
    sig = (term, topic)
    if st.session_state.get("qa_sig") != sig: st.session_state.update(qa_sig=sig, qa_n=12)
    n = st.session_state.get("qa_n", 12); grid(pool[:n])
    if len(pool) > n and st.button(f"Show 12 more ({len(pool) - n} left)"):
        st.session_state.qa_n = n + 12; st.rerun()
else:
    st.title("AI Assistant")
    key = st.sidebar.text_input("Anthropic API key", type="password", value=os.getenv("ANTHROPIC_API_KEY", ""))
    t_ask, t_week, t_dq = st.tabs(["Ask your data (Arabic)", "Weekly report", "Data-quality alerts"])
    need = "<div class='note'>Add your Anthropic API key in the sidebar (or set ANTHROPIC_API_KEY) to use this tab.</div>"

    def chart_for(df, k):
        num = [c for c in df.columns if c not in (df.columns[0], "change_%") and pd.api.types.is_numeric_dtype(df[c])]
        if num and len(df) > 1:
            st.plotly_chart(px.bar(df, x=df.columns[0], y=num, barmode="group"), width="stretch", key=k)

    with t_ask:
        st.caption("Examples: إيه مبيعات القاهرة آخر 30 يوم مقابل نفس الفترة السنة اللي فاتت؟ · أكتر قسم نزل مبيعاته؟ · هل التسويق مجدي؟")
        if not key: st.markdown(need, unsafe_allow_html=True)
        else:
            st.session_state.setdefault("chat", [])
            for m in st.session_state.chat: st.chat_message(m["role"]).markdown(m["text"])
            if prompt := st.chat_input("اسأل عن المبيعات أو الأرباح أو المخزون…"):
                st.chat_message("user").markdown(prompt)
                with st.spinner("Querying your tables…"):
                    text, used, _ = ai.ask(B, prompt, [{"role": m["role"], "content": m["text"]} for m in st.session_state.chat], key)
                with st.chat_message("assistant"):
                    st.markdown(text)
                    for n, (title, df) in enumerate(used):
                        with st.expander(f"Data behind the answer: {title}"): st.dataframe(df, width="stretch"); chart_for(df, f"ch{len(st.session_state.chat)}{n}")
                st.session_state.chat += [{"role": "user", "text": prompt}, {"role": "assistant", "text": text}]
    with t_week:
        facts = ai.weekly_facts(B)
        st.dataframe(pd.DataFrame(facts["weeks"]).set_index("week"), width="stretch")
        if not key: st.markdown(need, unsafe_allow_html=True)
        elif st.button("Generate weekly report (Arabic)"):
            with st.spinner("Writing report…"): st.session_state["report"] = ai.weekly_report(B, key)[0]
        if "report" in st.session_state:
            st.markdown(st.session_state["report"]); st.download_button("Download .md", st.session_state["report"], "weekly_report.md")
        st.caption("To get it automatically every week, schedule `python run_weekly.py`.")
    with t_dq:
        for a in ai.quality_alerts(B):
            st.markdown(f"<div class='note'><b>{a['severity']} · {a['title']}</b><br>{a['detail']}</div>", unsafe_allow_html=True)
