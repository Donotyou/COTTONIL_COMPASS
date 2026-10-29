# Cottonil Compass

An interactive business-health dashboard for Cottonil, an Egyptian cotton apparel company. It reads the company's CSV tables, cleans and joins them, and answers one question: **why does a company with a ~38% gross margin show a negative net profit?**

It combines three things:

- **68 live questions with charts.** Each chart comes with a written reading of the numbers and a short "So what" for decision-makers.
- **An Explorer page** with period, channel, governorate and category filters that update 16 linked charts together.
- **An AI assistant** that answers questions in Arabic or English by calling tools on your tables (the numbers are computed from the data, not from the model's memory).

Everything is computed from your files each time, so when the data changes the numbers change.

## Quick start

1. Install Python 3.10 or newer, then: `pip install -r requirements.txt`
2. Put the CSV tables in `./02_TABLES/` (and the catalog file in `./01_CATALOG/`), or point to them with the environment variables `COTTONIL_TABLES` and `COTTONIL_CATALOG`.
3. Run the app: `streamlit run app.py`
4. For the AI page, set a Google Gemini key: `GEMINI_API_KEY` (PowerShell: `$env:GEMINI_API_KEY="your-key"`). Everything else works without a key.

The first load takes a little longer because about 68 analyses are computed once and cached for the session.

## Required tables

The loader expects these CSV files (file name = table name) in `02_TABLES/`:

`sales_orders`, `sales_order_items`, `sku_variants`, `products_catalog`, `branches`, `customers`, `sales_returns`, `marketing_campaigns`, `operating_expenses`, `payroll`, `inventory_transfers`, `monthly_stock`, `purchase_orders`, `purchase_order_items`, `delivery_shipments`

Dates may be ISO (`2024-05-01`) or `M/D/YYYY`; both are handled in `data.py`.

## Pages

| Page | What it answers |
|---|---|
| Overview | Gauges (margin, marketing share, idle stock, discounts), ranked problems, key charts |
| Explorer | Free exploration with filters: trends, mix, products, geography |
| Profit & Loss | Monthly and yearly profit, cost structure, waterfall, seasonality, payroll completeness |
| Marketing | Cost per click, funnel, campaign efficiency, attributed vs real orders |
| Discounts | Discount depth, margin impact, break-even volume uplift |
| Sales & Concentration | Categories, channels, governorates, product hierarchy, weekday and size patterns |
| Customers & Branches | Loyalty, customer segments, best and weakest branches |
| Inventory & Purchasing | Months of cover, money tied up in stock, purchases vs sales, suppliers |
| Returns & Delivery | Return rates and reasons, carrier speed, delays by governorate |
| Questions & Answers | Searchable gallery of all questions |
| AI Assistant | Chat, weekly report, data-quality alerts |

## Project files

| File | Role |
|---|---|
| `app.py` | Streamlit pages and navigation |
| `config.py` | Paths and settings (see below) |
| `data.py` | Loading, date parsing, cleaning, the joined sales table |
| `analysis.py` | All calculations (P&L, marketing, discounts, stock, purchasing, returns) |
| `qa.py` | The 68 questions: each returns a written answer and a chart |
| `explorer.py` | Filterable Explorer page and gauge widgets |
| `ai.py` | AI assistant (tool calling), weekly report, rule-based data-quality alerts |
| `theme.py` | Design system: header, colours, widget styling, Plotly template |
| `verify.py` | Checks the app's numbers (see Verification) |
| `export_story.py` | Exports key facts and written answers to `story_facts.md` for presentations |
| `run_weekly.py` | Generates the weekly report as a file, for scheduling |
| `.streamlit/config.toml` | Base theme colours |
| `assets/logo.png` | Optional. Replaces the built-in logo in the header |

## Settings (`config.py`)

- `TABLES_PATH`, `CATALOG_PATH`: data folders.
- `EXCLUDE_OPEX_MARKETING = True`: removes the "Marketing" line from operating expenses so marketing is not counted twice (the campaigns table is the reference).
- `RECENT_MONTHS = 3`: window used to compare recent months with the best period.
- `MODEL` / `GEMINI_MODEL`: the AI model. If you hit free-tier rate limits, try `gemini-2.5-flash-lite`.

## How the numbers are built

- Revenue is `net_line_EGP` (before tax). Gross profit is `margin_EGP`.
- The first and last months of the data are partial and are excluded from trends; only full months enter the P&L.
- Marketing spend is spread evenly over each campaign's days.
- Net profit is an **estimate**. It excludes import and shipping costs.
- "Attributed orders" in the campaigns table are shown for transparency but are **not** used to judge return on spend (see Data notes).

## Verification

```
python verify.py
```

It prints two blocks:

1. 21 metrics computed by the app next to the values from the original analysis notebook, each marked PASS or CHECK. The expected values inside `verify.py` belong to the original dataset; if the data changes, update them.
2. Independent checks computed straight from the raw tables (order count, revenue, units, refunds, marketing spend). The marketing check is expected to differ slightly because partial months are excluded.

## Weekly report and presentation export

- `python run_weekly.py` writes `reports/weekly_<date>.md` (needs the AI key). Schedule it with cron or Windows Task Scheduler.
- `python export_story.py` writes `story_facts.md` with all key numbers, the yearly P&L, data alerts and every written answer. Install `kaleido` (`pip install kaleido`) to also export each chart as a PNG.

## AI assistant

The assistant calls two tools on your tables: a sales query tool (revenue, orders, units, gross profit by period, governorate, category, channel, branch or product family) and a finance tool (P&L, marketing, discounts, stock, returns, alerts). It replies in the language of the question.

Privacy: only the tool results (up to 25 rows per call) and your question are sent to the AI provider. The full tables stay on your machine. Check that this is acceptable for your data before using it with company information.

Treat answers as a starting point and confirm important numbers on the Explorer or Questions pages.

## Data notes (read before presenting)

The analysis surfaced several data issues that change how results should be read:

- **Purchases do not match sales.** About 339 million units were bought against 3.4 million sold (about 100x), and purchase cost is about 56x cost of goods sold. This is likely a scale or data-entry problem and must be checked at the source.
- **Attributed orders are overstated.** Campaigns claim about 24 million orders against 540 thousand real orders (about 44x), and each campaign receives roughly 5% of its clicks as orders. The figure looks formula-derived, not tracked.
- **Payroll for the latest year looks incomplete**, so recent profit may be overstated.
- **Stock cover is extreme** and the stock-out risk score does not follow real cover. Confirm the stock table's scale.
- Some sentences in the written answers use fixed wording based on the current dataset (for example "most growth is price-driven"). Re-read them against the chart if the data changes.

These are shown in the AI page under "Data-quality alerts" and are computed live.

## Troubleshooting

- `ModuleNotFoundError`: run commands from the project folder and reinstall with `pip install -r requirements.txt`.
- Empty app or load error: check `TABLES_PATH` and that the file names match the table list above.
- AI rate-limit message: wait a minute or switch to a lighter model in `config.py`.
