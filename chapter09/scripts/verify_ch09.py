"""Independent, read-only checks of Chapter09 numeric and procedural evidence."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.regression import FEATURE_COLUMNS, FORBIDDEN_FEATURES, validate_feature_columns


def main():
    report = ROOT / "reports"
    manifest = json.loads((ROOT / "source_manifest.json").read_text(encoding="utf-8"))
    checks = []

    def check(name, ok):
        checks.append({"check": name, "status": "PASS" if ok else "FAIL"})
        assert ok, name

    for filename, expected in manifest["raw_sha256"].items():
        check("raw_unchanged_" + filename, hashlib.sha256((ROOT / "data/raw" / filename).read_bytes()).hexdigest() == expected)
    model_data = pd.read_csv(report / "ch09_regression_model_data_internal.csv", parse_dates=["order_date"])
    items = pd.read_csv(ROOT / "data/raw/order_items.csv")
    expected_total = (items.quantity * items.unit_price).groupby(items.order_id).sum()
    check("all_order_targets_match_raw", np.array_equal(model_data.order_total, model_data.order_id.map(expected_total)))
    split = pd.read_csv(report / "ch09_regression_split_summary.csv")
    cutoff = pd.Timestamp(split.loc[split.split.eq("test"), "start_date"].iloc[0])
    train = model_data.loc[model_data.order_date < cutoff].reset_index(drop=True)
    test = model_data.loc[model_data.order_date >= cutoff].reset_index(drop=True)
    check("strict_dates", train.order_date.max() < test.order_date.min())
    check("train_test_rows", len(train) == int(split.iloc[0].rows) and len(test) == int(split.iloc[1].rows))
    cv = pd.read_csv(report / "ch09_regression_cv_summary.csv")
    frozen = json.loads((report / "ch09_model_selection_frozen.json").read_text(encoding="utf-8"))
    candidates = cv[cv.model.ne("Baseline Mean")].sort_values(["cv_MAE_mean", "model"])
    check("train_cv_selected_model", frozen["selected_model"] == candidates.iloc[0].model and not frozen["final_test_used_for_selection"])
    check("feature_overlap_zero", set(frozen["features"]) == set(FEATURE_COLUMNS) and not set(frozen["features"]) & FORBIDDEN_FEATURES)
    try:
        validate_feature_columns([*FEATURE_COLUMNS, "quantity"])
    except ValueError:
        check("forbidden_feature_rejected", True)
    else:
        check("forbidden_feature_rejected", False)

    fold_rows = []
    for fold, (tr, va) in enumerate(TimeSeriesSplit(n_splits=5).split(train), start=1):
        y_tr, y_va = train.iloc[tr].order_total, train.iloc[va].order_total
        fold_rows.append({"fold": fold, "train_rows": len(tr), "validation_rows": len(va),
            "train_end": str(train.iloc[tr].order_date.max().date()),
            "validation_start": str(train.iloc[va].order_date.min().date()),
            "overlapping_calendar_days": len(set(train.iloc[tr].order_date) & set(train.iloc[va].order_date)),
            "baseline_MAE": np.abs(y_va - y_tr.mean()).mean()})
    folds = pd.DataFrame(fold_rows)
    check("baseline_cv_independent", np.isclose(folds.baseline_MAE.mean(), cv.loc[cv.model.eq("Baseline Mean"), "cv_MAE_mean"].iloc[0]))
    folds.to_csv(report / "ch09_cv_fold_checks.csv", index=False, encoding="utf-8-sig")

    metrics = pd.read_csv(report / "ch09_regression_model_comparison.csv")
    check("exact_final_models", set(metrics.model) == {"Baseline Mean", frozen["selected_model"]} and len(metrics) == 2)
    pred = pd.read_csv(report / "ch09_regression_predictions_internal.csv")
    check("prediction_covers_final_test", set(pred.order_id) == set(test.order_id) and len(pred) == len(test))
    check("prediction_actual_matches_raw", np.array_equal(pred.actual_order_total, pred.order_id.map(expected_total)))
    residual = pred.actual_order_total - pred.predicted_order_total
    check("residual_abs_error", np.allclose(pred.residual, residual) and np.allclose(pred.abs_error, np.abs(residual)))
    baseline_error = test.order_total.to_numpy() - train.order_total.mean()
    selected = metrics[metrics.model.eq(frozen["selected_model"])].iloc[0]
    baseline = metrics[metrics.model.eq("Baseline Mean")].iloc[0]
    denominator = np.square(test.order_total - test.order_total.mean()).sum()
    for name, row, errors in [("baseline", baseline, baseline_error), ("selected", selected, residual.to_numpy())]:
        expected = [np.abs(errors).mean(), np.sqrt(np.square(errors).mean()), 1 - np.square(errors).sum()/denominator]
        check(name + "_all_metrics", np.allclose([row.test_MAE, row.test_RMSE, row.test_R2], expected, rtol=1e-9, atol=1e-6))
    check("improvement_formula", np.isclose(selected.MAE_improvement_vs_baseline_pct, round((baseline.test_MAE-selected.test_MAE)/baseline.test_MAE*100, 2)))
    public = pd.read_csv(report / "ch09_regression_predictions_public.csv")
    check("public_columns_safe", not set(public.columns) & {"order_id", "customer_id", "name", "email", "phone", "address"})
    check("official_validation", pd.read_csv(report / "ch09_regression_validation.csv").status.eq("PASS").all())
    pd.DataFrame(checks).to_csv(report / "ch09_independent_validation.csv", index=False, encoding="utf-8-sig")
    print(pd.DataFrame(checks).to_string(index=False))
    print(f"Independent validation: {len(checks)} PASS")


if __name__ == "__main__":
    main()
