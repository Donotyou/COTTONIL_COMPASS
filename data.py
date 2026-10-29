import os
import pandas as pd
from config import TABLES_PATH, CATALOG_PATH

DATE_COLS = {
    "branches": ["opening_date"], "customers": ["joined_date"], "delivery_shipments": ["ship_date", "delivery_date"],
    "inventory_transfers": ["transfer_date"], "marketing_campaigns": ["start_date", "end_date"],
    "operating_expenses": ["expense_date"], "purchase_orders": ["po_date"], "sales_orders": ["order_date"],
    "sales_order_items": ["order_date"], "sales_payments": ["payment_date"], "sales_returns": ["return_date"],
}

def _parse(s):
    s = s.astype(str).str.strip()
    iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    mdy = pd.to_datetime(s, format="%m/%d/%Y", errors="coerce")
    return iso.fillna(mdy).fillna(pd.to_datetime(s, errors="coerce"))

def load():
    data = {f[:-4]: pd.read_csv(os.path.join(TABLES_PATH, f)) for f in os.listdir(TABLES_PATH) if f.endswith(".csv")}
    for t, cols in DATE_COLS.items():
        for c in cols:
            if t in data and c in data[t]:
                data[t][c] = _parse(data[t][c])
    return data

def build(data):
    o, it = data["sales_orders"].copy(), data["sales_order_items"]
    o["customer_id"] = o["customer_id"].fillna("GUEST")
    sku = data["sku_variants"].drop(columns=["product_id"])
    br = data["branches"][["branch_id", "branch_name_ar", "governorate_ar"]]
    f = (it.drop(columns=["order_date", "branch_id"])
         .merge(o[["sales_order_id", "order_date", "branch_id", "customer_id", "sales_channel"]], on="sales_order_id", how="left")
         .merge(sku, on="sku_id", how="left")
         .merge(data["products_catalog"][["product_id", "product_name_ar", "category_en"]], on="product_id", how="left")
         .merge(br, on="branch_id", how="left"))
    f["product_family"] = f["product_name_ar"].str.replace(r"\s*\d+$", "", regex=True).str.strip()
    f["cogs_EGP"] = f["unit_cost_EGP"] * f["quantity"]
    f["month"] = f["order_date"].dt.to_period("M")
    f["year"] = f["order_date"].dt.year
    d0, d1 = f["order_date"].min(), f["order_date"].max()
    full = [m for m in pd.period_range(d0, d1, freq="M") if m.start_time >= d0 and m.end_time.normalize() <= d1]
    return dict(data=data, orders=o, fact=f, fact_full=f[f["month"].isin(full)].copy(), full_months=full, _c={})
