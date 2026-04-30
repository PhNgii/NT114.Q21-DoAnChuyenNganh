import json
import sys
from pathlib import Path

import pandas as pd

if len(sys.argv) < 2:
    print("Usage: python scripts/fit_latency_calibration.py eval/calibration_file.csv")
    sys.exit(1)

csv_path = sys.argv[1]
df = pd.read_csv(csv_path)

required = ["actual_latency", "predicted_latency", "predicted_status"]
df = df.dropna(subset=required).copy()

df["residual"] = df["actual_latency"] - df["predicted_latency"]

offsets = {}

for status, group in df.groupby("predicted_status"):
    offsets[status] = round(float(group["residual"].mean()), 4)

# fallback nếu thiếu class nào đó
for status in ["Good", "Warning", "Critical"]:
    offsets.setdefault(status, 0.0)

out_path = Path("models/latency_calibration.json")
out_path.parent.mkdir(exist_ok=True)

with out_path.open("w", encoding="utf-8") as f:
    json.dump(offsets, f, indent=2)

print("Saved calibration offsets to:", out_path)
print(json.dumps(offsets, indent=2))
