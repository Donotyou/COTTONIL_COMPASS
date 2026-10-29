"""Cottonil design system — drop-in replacement for theme.py.

Same API as before: call theme.apply() once at the top of app.py.
It now also draws the branded header (logo + company name).

Custom logo: put your own file at  assets/logo.png  (or logo.svg / logo.jpg)  and it replaces the built-in mark.
"""
import base64
import os

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ----------------------------------------------------------------------------- brand settings
BRAND = "COTTONIL"
TAGLINE = "Compass · Business Health Center"
LOGO_FILES = ["assets/logo.png", "assets/logo.svg", "assets/logo.jpg"]

# ----------------------------------------------------------------------------- palette (coordinated pastel family + strong data colours)
INK, INK2 = "#0F2742", "#34506E"
BLUE = dict(l="#E8F3FF", m="#BFDDFB", s="#3B8FE0", d="#1F5FA8")
PINK = dict(l="#FFEAF1", m="#FAC8DA", s="#E5648A")
ORANGE = dict(l="#FFF0DE", m="#FFD3A3", s="#F59A3D")
MINT = dict(l="#DDF5EE", s="#2EAF94")
PURPLE = "#8B6FD6"
PALETTE = [BLUE["s"], ORANGE["s"], PINK["s"], MINT["s"], PURPLE, "#5C7FA3", "#E0B52E"]

# ----------------------------------------------------------------------------- Plotly template
pio.templates["cc"] = go.layout.Template(layout=dict(
    colorway=PALETTE,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white",
    font=dict(family="Inter, Cairo, Arial", size=14, color=INK),
    title_font=dict(size=16, color=INK),
    xaxis=dict(gridcolor="#E3ECF5", linecolor="#BFD3E8", zeroline=False, tickfont=dict(size=13), title_font=dict(size=13)),
    yaxis=dict(gridcolor="#E3ECF5", linecolor="#BFD3E8", zeroline=False, tickfont=dict(size=13), title_font=dict(size=13)),
    legend=dict(orientation="h", y=1.12, x=0, font=dict(size=13), bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="white", bordercolor=BLUE["s"], font=dict(size=13, color=INK)),
    margin=dict(l=10, r=10, t=40, b=10),
    colorscale=dict(sequential=[[0, BLUE["l"]], [0.5, BLUE["m"]], [1, BLUE["d"]]],
                    diverging=[[0, PINK["s"]], [0.5, "#FFFFFF"], [1, BLUE["s"]]]),
))
pio.templates.default = "cc"

# ----------------------------------------------------------------------------- logo
_SVG_LOGO = """<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}">
<defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#BFDDFB"/><stop offset=".55" stop-color="#FAC8DA"/><stop offset="1" stop-color="#FFD3A3"/></linearGradient></defs>
<rect width="64" height="64" rx="18" fill="url(#lg)"/>
<path d="M32 54 C32 44 32 40 32 34" stroke="#2EAF94" stroke-width="3" stroke-linecap="round" fill="none"/>
<path d="M32 46 C26 45 22 41 21 37 C27 37 31 40 32 46Z M32 44 C38 43 42 39 43 35 C37 35 33 38 32 44Z" fill="#2EAF94"/>
<g fill="#FFFFFF" stroke="#3B8FE0" stroke-width="1.6"><circle cx="32" cy="14" r="7.2"/><circle cx="22.5" cy="21" r="7.2"/><circle cx="41.5" cy="21" r="7.2"/><circle cx="26" cy="31" r="7.2"/><circle cx="38" cy="31" r="7.2"/></g>
<circle cx="32" cy="23" r="6.4" fill="#FFFFFF"/><circle cx="32" cy="23" r="2.4" fill="#F59A3D"/></svg>"""

def _logo_html(size=52):
    for p in LOGO_FILES:
        if os.path.exists(p):
            mime = "image/svg+xml" if p.endswith(".svg") else "image/png" if p.endswith(".png") else "image/jpeg"
            b64 = base64.b64encode(open(p, "rb").read()).decode()
            return f'<img src="data:{mime};base64,{b64}" width="{size}" height="{size}" style="border-radius:16px;object-fit:contain;background:#fff;padding:4px"/>'
    return _SVG_LOGO.replace("{s}", str(size))

# ----------------------------------------------------------------------------- CSS
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600;700&family=Cairo:wght@500;700&display=swap');
:root{--ink:#0F2742;--ink2:#34506E;--b1:#E8F3FF;--b2:#BFDDFB;--b3:#3B8FE0;--b4:#1F5FA8;--p1:#FFEAF1;--p2:#FAC8DA;--p3:#E5648A;
--o1:#FFF0DE;--o2:#FFD3A3;--o3:#F59A3D;--m1:#DDF5EE;--m3:#2EAF94;--line:#D3E4F6;--shadow:0 8px 24px rgba(31,95,168,.10)}
html,body,.stApp,button,input,textarea{font-family:'Inter','Cairo','Segoe UI',sans-serif}
.stApp{background:
 radial-gradient(900px 420px at 0% -6%,var(--b1) 0%,transparent 62%),
 radial-gradient(820px 400px at 100% 0%,var(--p1) 0%,transparent 62%),
 radial-gradient(1000px 520px at 50% 118%,var(--o1) 0%,transparent 62%),#FFFFFF;background-attachment:fixed}
.block-container{padding-top:1.1rem;max-width:1300px}
footer{visibility:hidden}
.stApp,.stApp p,.stApp li,.stApp label,.stApp span,.stApp div{color:var(--ink)}
.stApp p,.stApp li{font-size:16px;line-height:1.65;font-weight:500}
[data-testid=stCaptionContainer],[data-testid=stCaptionContainer] p{color:var(--ink2)!important;font-size:14px!important;font-weight:500}
h1,h2,h3,h4,h5{color:var(--ink)!important;font-family:'Poppins','Inter','Cairo',sans-serif!important;font-weight:700!important;letter-spacing:-.2px}
h1{font-size:2.1rem!important;padding-bottom:.55rem;position:relative}
h1::after{content:"";position:absolute;left:0;bottom:0;width:84px;height:5px;border-radius:9px;background:linear-gradient(90deg,var(--b3),var(--p3),var(--o3))}
h4{font-size:1.08rem!important;margin-bottom:.2rem}
a{color:var(--b4)!important;font-weight:600}
::selection{background:var(--p2)}

/* ---------- header ---------- */
.cc-header{position:relative;overflow:hidden;display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;
 padding:18px 26px;margin:0 0 20px;border-radius:24px;border:1px solid var(--line);box-shadow:var(--shadow);
 background:linear-gradient(120deg,var(--b1) 0%,#FFFFFF 38%,var(--p1) 68%,var(--o1) 100%)}
.cc-header::before{content:"";position:absolute;right:-60px;top:-70px;width:220px;height:220px;border-radius:50%;background:radial-gradient(circle,var(--p2) 0%,transparent 70%);opacity:.7}
.cc-header::after{content:"";position:absolute;left:30%;bottom:-90px;width:260px;height:200px;border-radius:50%;background:radial-gradient(circle,var(--b2) 0%,transparent 70%);opacity:.6}
.cc-brand{display:flex;align-items:center;gap:16px;position:relative;z-index:1}
.cc-name{font-family:'Poppins',sans-serif;font-weight:800;font-size:1.9rem;letter-spacing:3px;line-height:1.05;color:var(--ink)}
.cc-name b{background:linear-gradient(90deg,var(--b3),var(--p3));-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent}
.cc-tag{font-size:.9rem;font-weight:600;color:var(--ink2);letter-spacing:.6px;margin-top:2px}
.cc-chips{display:flex;gap:8px;flex-wrap:wrap;position:relative;z-index:1}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:.8rem;font-weight:700;padding:6px 14px;border-radius:999px;border:1px solid;background:#fff}
.chip::before{content:"";width:8px;height:8px;border-radius:50%;background:currentColor}
.chip.b{color:var(--b4);border-color:var(--b2);background:var(--b1)}
.chip.p{color:#B83A62;border-color:var(--p2);background:var(--p1)}
.chip.o{color:#B56A12;border-color:var(--o2);background:var(--o1)}

/* ---------- sidebar ---------- */
[data-testid=stSidebar]{background:linear-gradient(180deg,var(--b1) 0%,#FFFFFF 55%,var(--p1) 100%);border-right:1px solid var(--line)}
[data-testid=stSidebar] h2{font-size:1.25rem!important}
[data-testid=stSidebar] [role=radiogroup]{gap:4px}
[data-testid=stSidebar] label[data-baseweb=radio]{padding:9px 14px;border-radius:14px;border:1px solid transparent;transition:all .15s ease;width:100%}
[data-testid=stSidebar] label[data-baseweb=radio]:hover{background:rgba(255,255,255,.85);border-color:var(--b2)}
[data-testid=stSidebar] label[data-baseweb=radio] > div:first-child{display:none}
[data-testid=stSidebar] label[data-baseweb=radio] p{font-weight:600;font-size:15px}
[data-testid=stSidebar] label[data-baseweb=radio]:has(input:checked){background:#fff;border-color:var(--b3);box-shadow:0 4px 14px rgba(59,143,224,.18);border-left:6px solid var(--o3)}
[data-testid=stSidebar] label[data-baseweb=radio]:has(input:checked) p{color:var(--b4);font-weight:700}

/* ---------- KPI cards (st.metric) ---------- */
[data-testid=stMetric]{background:#fff;border:1px solid var(--line);border-top:5px solid var(--b3);border-radius:18px;padding:14px 18px;box-shadow:var(--shadow);position:relative;overflow:hidden}
[data-testid=stMetric]::after{content:"";position:absolute;right:-26px;top:-26px;width:90px;height:90px;border-radius:50%;background:var(--b1);opacity:.9}
[data-testid=stMetricValue]{font-family:'Poppins',sans-serif;font-weight:800;font-size:2rem;position:relative;z-index:1}
[data-testid=stMetricLabel] p{font-weight:700;color:var(--ink2);position:relative;z-index:1}
[data-testid=stHorizontalBlock]>div:nth-child(2) [data-testid=stMetric]{border-top-color:var(--p3)}
[data-testid=stHorizontalBlock]>div:nth-child(2) [data-testid=stMetric]::after{background:var(--p1)}
[data-testid=stHorizontalBlock]>div:nth-child(3) [data-testid=stMetric]{border-top-color:var(--o3)}
[data-testid=stHorizontalBlock]>div:nth-child(3) [data-testid=stMetric]::after{background:var(--o1)}
[data-testid=stHorizontalBlock]>div:nth-child(4) [data-testid=stMetric]{border-top-color:var(--m3)}
[data-testid=stHorizontalBlock]>div:nth-child(4) [data-testid=stMetric]::after{background:var(--m1)}

/* ---------- chart cards (st.container(border=True)) ---------- */
[data-testid=stVerticalBlockBorderWrapper]:has(.js-plotly-plot),[data-testid=stVerticalBlockBorderWrapper]:has([data-testid=stPlotlyChart]){
 background:#fff;border:1px solid var(--line)!important;border-radius:20px!important;box-shadow:var(--shadow);transition:transform .15s ease,box-shadow .15s ease}
[data-testid=stVerticalBlockBorderWrapper]:has([data-testid=stPlotlyChart]):hover{transform:translateY(-2px);box-shadow:0 14px 30px rgba(31,95,168,.16)}
[data-testid=stVerticalBlockBorderWrapper] h4::before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:9px;background:linear-gradient(135deg,var(--b3),var(--p3))}

/* ---------- notes ---------- */
.note{background:var(--o1);border:1px solid var(--o2);border-left:6px solid var(--o3);border-radius:14px;padding:12px 16px;margin:8px 0;font-size:15.5px;font-weight:500}
.note.blue{background:var(--b1);border-color:var(--b2);border-left-color:var(--b3)}
.note.pink{background:var(--p1);border-color:var(--p2);border-left-color:var(--p3)}
.note.mint{background:var(--m1);border-color:#B6E6D8;border-left-color:var(--m3)}

/* ---------- widgets ---------- */
button[data-baseweb=tab]{border-radius:12px 12px 0 0;font-weight:700;padding:8px 18px}
button[data-baseweb=tab][aria-selected=true]{background:var(--b1);color:var(--b4)}
div[data-baseweb=tab-highlight]{background:linear-gradient(90deg,var(--b3),var(--o3));height:4px;border-radius:4px}
.stButton>button,.stDownloadButton>button{background:linear-gradient(120deg,var(--o2),var(--p2));color:var(--ink);border:1px solid var(--o2);
 border-radius:999px;font-weight:700;padding:.5rem 1.4rem;box-shadow:0 4px 12px rgba(245,154,61,.22);transition:all .15s ease}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-1px);box-shadow:0 8px 18px rgba(229,100,138,.28);border-color:var(--p3);color:var(--ink)}
div[data-baseweb=select]>div,div[data-baseweb=input]>div,textarea{border-radius:12px!important;border-color:var(--b2)!important;background:#fff!important}
[data-testid=stChatMessage]{background:#fff;border:1px solid var(--line);border-radius:18px;padding:12px 16px;margin-bottom:10px;box-shadow:0 4px 14px rgba(31,95,168,.06)}
[data-testid=stChatMessage]:has([data-testid=stChatMessageAvatarUser]){background:var(--b1)}
[data-testid=stChatMessage]:has([data-testid=stChatMessageAvatarAssistant]){background:var(--p1)}
[data-testid=stExpander]{border:1px solid var(--line)!important;border-radius:14px!important;background:#fff}
[data-testid=stDataFrame]{border:1px solid var(--line);border-radius:14px;overflow:hidden}
[data-testid=stAlert]{border-radius:14px}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-thumb{background:var(--b2);border-radius:10px}::-webkit-scrollbar-track{background:var(--b1)}
@media (max-width:768px){.cc-name{font-size:1.4rem}.cc-header{padding:14px 16px}}
.banner{display:flex;align-items:center;gap:16px;padding:16px 22px;border-radius:20px;margin:4px 0 14px;border:1px solid var(--line);box-shadow:var(--shadow)}
.banner .ic{font-size:2rem;width:56px;height:56px;border-radius:16px;display:grid;place-items:center;background:#fff;box-shadow:0 4px 12px rgba(31,95,168,.12)}
.banner h2{margin:0!important;font-size:1.5rem!important}.banner p{margin:2px 0 0;color:var(--ink2);font-weight:600}
.banner.blue{background:linear-gradient(110deg,var(--b1),#fff)}.banner.pink{background:linear-gradient(110deg,var(--p1),#fff)}.banner.orange{background:linear-gradient(110deg,var(--o1),#fff)}.banner.mint{background:linear-gradient(110deg,var(--m1),#fff)}
.tkgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:0 0 16px}
.tk{background:#fff;border:1px solid var(--line);border-radius:16px;padding:12px 16px;box-shadow:0 4px 14px rgba(31,95,168,.07);font-size:14.5px;font-weight:600;line-height:1.5}
.tk small{display:block;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--ink2);margin-bottom:4px}
.tk:nth-child(1){border-top:4px solid var(--b3)}.tk:nth-child(2){border-top:4px solid var(--p3)}.tk:nth-child(3){border-top:4px solid var(--o3)}.tk:nth-child(4){border-top:4px solid var(--m3)}
.stApp [data-testid=stSelectSlider]{padding:2px 8px}
</style>"""

CSS = "\n".join(l for l in CSS.splitlines() if l.strip())   # no blank lines inside the HTML block

def header():
    st.markdown(
        f'<div class="cc-header"><div class="cc-brand">{_logo_html(56)}'
        f'<div><div class="cc-name">COTT<b>ONIL</b></div><div class="cc-tag">{TAGLINE}</div></div></div>'
        '<div class="cc-chips"><span class="chip b">Live from your tables</span><span class="chip p">AI-assisted</span>'
        '<span class="chip o">Decision-ready insights</span></div></div>', unsafe_allow_html=True)

def banner(title, subtitle, icon="📊", tone="blue"):
    st.markdown(f'<div class="banner {tone}"><div class="ic">{icon}</div><div><h2>{title}</h2><p>{subtitle}</p></div></div>', unsafe_allow_html=True)

def takeaways(items):
    """Row of short insight cards; items = list of strings."""
    st.markdown('<div class="tkgrid">' + "".join(f'<div class="tk"><small>Key takeaway {i}</small>{t}</div>' for i, t in enumerate(items, 1)) + '</div>', unsafe_allow_html=True)

def callout(text, tone=""):
    """Coloured note box. tone: '' (orange) | 'blue' | 'pink' | 'mint'."""
    st.markdown(f"<div class='note {tone}'>{text}</div>", unsafe_allow_html=True)

def apply(show_header=True):
    st.markdown(CSS, unsafe_allow_html=True)
    if show_header:
        header()
