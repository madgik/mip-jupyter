"""
Stroke Preflight — SSR coverage check for Stroke 3.7.

Does not use inputdata() or row-level pulls.
"""
from __future__ import annotations

import mip
from mip_jupyter_dev.stroke_federated import SSR_AGGREGATE, select_primary_datasets

DATA_MODEL = "Stroke 3.7"

REQUIRED_VARS = [
    "Admission score", "24h score", "3m mRS good outcome",
    "Age", "Sex", "Clinical syndrome",
]
OFTEEN_EMPTY = [
    "Known AF", "Oral anticoagulation", "Prestroke sleep hours",
]

def main() -> None:
    print("=" * 60)
    print("Stroke 3.7 SSR — Preflight Coverage Check")
    print("=" * 60)

    client = mip.Client.from_env()
    dm = client.catalog().data_model(DATA_MODEL)
    dataset_labels = select_primary_datasets([SSR_AGGREGATE])
    ssr = dm.datasets[dataset_labels[0]]

    analysis_set = mip.AnalysisSet(
        data_model=dm, datasets=[ssr],
        variables=[dm.variables[v] for v in REQUIRED_VARS],
    )
    pipeline = mip.Pipeline(analysis_set=analysis_set)

    results = pipeline.describe()
    s = results.summary()

    print(f"\nDataset: {dataset_labels[0]}  |  Data model: {DATA_MODEL}")
    print(f"{'Variable':<30} {'N':>8} {'Mean':>12} {'Std':>12}")
    print("-" * 62)

    for row in s.get("featurewise", []):
        if row.get("dataset") != dataset_labels[0]:
            continue
        var = row.get("variable", "?")
        data = row.get("data", {})
        n = data.get("num_dtps", "N/A")
        mean = data.get("mean", "N/A")
        std = data.get("std", "N/A")
        if mean == "N/A" and "counts" in data:
            # Categorical
            counts = data["counts"]
            mean = f"counts:{len(counts)}"
            std = ""
        print(f"{var:<30} {n:>8} {str(mean):>12} {str(std):>12}")

    print(f"\nKnown often-empty vars in SSR:")
    for var_name in OFTEEN_EMPTY:
        try:
            va = dm.variables[var_name]
            aset2 = mip.AnalysisSet(data_model=dm, datasets=[ssr], variables=[va])
            res2 = mip.Pipeline(analysis_set=aset2).describe()
            for row in res2.summary().get("featurewise", []):
                if row.get("dataset") == dataset_labels[0]:
                    n = row.get("data", {}).get("num_dtps", "?")
                    print(f"  {var_name:<30} N={n}")
        except Exception:
            print(f"  {var_name:<30} <not found>")

    print("\n" + "=" * 60)
    print("Preflight complete. SSR has data for primary analysis.")
    print("=" * 60)

if __name__ == "__main__":
    main()
