"""Independent checks: reconstruct aggregates without the project module."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    raw = ROOT / "data/raw"
    out = ROOT / "reports"
    manifest = json.loads((ROOT / "source_manifest.json").read_text(encoding="utf-8"))
    checks = []

    def check(name, passed):
        checks.append({"check": name, "status": "PASS" if passed else "FAIL"})
        assert passed, name

    for name, expected in manifest["raw_sha256"].items():
        check("raw_unchanged_" + name, hashlib.sha256((raw / name).read_bytes()).hexdigest() == expected)

    orders = pd.read_csv(raw / "orders.csv").set_index("order_id")
    products = pd.read_csv(raw / "products.csv").set_index("product_id")
    customers = pd.read_csv(raw / "customers.csv").set_index("customer_id")
    items = pd.read_csv(raw / "order_items.csv")
    # These pinned official sample inputs contain no missing values or duplicates.
    check("raw_no_missing_or_duplicate_rows", all(
        not df.isna().any().any() and not df.reset_index().duplicated().any()
        for df in (orders, products, customers, items)
    ))
    items["status"] = items.order_id.map(orders.order_status)
    completed = items.loc[items.status.eq("completed")].copy()
    completed["amount"] = completed.quantity * completed.unit_price
    completed["category"] = completed.product_id.map(products.category)
    completed["month"] = pd.to_datetime(completed.order_id.map(orders.order_date)).dt.strftime("%Y-%m")
    completed["customer"] = completed.order_id.map(orders.customer_id)
    total = completed.amount.sum()

    for group, file in (("category", "ch08_category_sales.csv"), ("month", "ch08_monthly_sales.csv")):
        original_key = "order_month" if group == "month" else group
        saved = pd.read_csv(out / file).set_index(original_key).total_sales.sort_index()
        expected = completed.groupby(group).amount.sum().sort_index()
        check(group + "_all_amounts", saved.index.tolist() == expected.index.tolist() and np.allclose(saved, expected, rtol=0, atol=1e-6))
        if group == "month":
            counts = pd.read_csv(out / file).set_index(original_key).order_count.sort_index()
            check("monthly_unique_orders", counts.tolist() == completed.groupby(group).order_id.nunique().sort_index().tolist())

    saved_c = pd.read_csv(out / "ch08_customer_sales.csv")
    expected_c = completed.groupby("customer").amount.sum().sort_values(ascending=False).to_numpy()
    check("customer_ranked_amounts", np.array_equal(saved_c.total_sales.to_numpy(), expected_c))
    check("public_customer_columns", set(saved_c.columns) == {"customer_label", "city", "order_count", "total_sales", "avg_order_value"})
    check("rank_based_labels", saved_c.customer_label.tolist() == [f"Customer {i:02d}" for i in range(1,len(saved_c)+1)])
    check("four_way_total", all(np.isclose(pd.read_csv(out / file).total_sales.sum(), total) for file in ("ch08_category_sales.csv", "ch08_monthly_sales.csv", "ch08_customer_sales.csv")))
    check("official_validation_all_pass", pd.read_csv(out / "ch08_project_validation.csv").status.eq("PASS").all())
    pd.DataFrame(checks).to_csv(out / "ch08_independent_checks.csv", index=False, encoding="utf-8-sig")
    print(pd.DataFrame(checks).to_string(index=False))
    print(f"Independent checks: {len(checks)} PASS; completed total = {total:,.0f} KRW")


if __name__ == "__main__":
    main()
