import json
import sys
import math
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    r2_score,
)

if len(sys.argv) < 2:
    print("Usage: python scripts/evaluate_calibrated_aws_eval.py eval/test_file.csv")
    sys.exit(1)

csv_path = sys.argv[1]
calibration_path = "models/latency_calibration.json"

df = pd.read_csv(csv_path)

with open(calibration_path, "r", encoding="utf-8") as f:
    offsets = json.load(f)

df = df.dropna(subset=["actual_latency", "predicted_latency", "predicted_status", "true_status"]).copy()

def apply_calibration(row):
    status = row["predicted_status"]
    offset = offsets.get(status, 0.0)
    return row["predicted_latency"] + offset

df["calibrated_predicted_latency"] = df.apply(apply_calibration, axis=1)
df["calibrated_latency_error"] = (df["actual_latency"] - df["calibrated_predicted_latency"]).abs()

actual = df["actual_latency"].astype(float).values
pred = df["calibrated_predicted_latency"].astype(float).values

errors = np.abs(actual - pred)

mae = errors.mean()
rmse = math.sqrt(((actual - pred) ** 2).mean())
mape = np.mean(np.abs((actual - pred) / actual)) * 100
approx_accuracy = max(0, 100 - mape)
r2 = r2_score(actual, pred)

acc_5 = np.mean(errors <= 5) * 100
acc_10 = np.mean(errors <= 10) * 100
acc_20 = np.mean(errors <= 20) * 100
acc_30 = np.mean(errors <= 30) * 100

status_acc = accuracy_score(df["true_status"], df["predicted_status"]) * 100

print("========== CALIBRATED AWS EVALUATION RESULT ==========")
print(f"File: {csv_path}")
print(f"Calibration file: {calibration_path}")
print(f"Samples: {len(df)}")
print()
print("Latency Regression After Calibration:")
print(f"MAE: {mae:.2f} ms")
print(f"RMSE: {rmse:.2f} ms")
print(f"MAPE: {mape:.2f}%")
print(f"Approx Accuracy: {approx_accuracy:.2f}%")
print(f"R2 Score: {r2:.4f}")

print()
print("Tolerance Accuracy After Calibration:")
print(f"Within ±5 ms : {acc_5:.2f}%")
print(f"Within ±10 ms: {acc_10:.2f}%")
print(f"Within ±20 ms: {acc_20:.2f}%")
print(f"Within ±30 ms: {acc_30:.2f}%")

print()
print("Status Classification:")
print(f"Status Accuracy: {status_acc:.2f}%")
print(classification_report(df["true_status"], df["predicted_status"], zero_division=0))

labels = ["Good", "Warning", "Critical"]
print("Confusion Matrix:")
print(confusion_matrix(df["true_status"], df["predicted_status"], labels=labels))

print()
print("Preview:")
print(df[[
    "scenario",
    "actual_latency",
    "predicted_latency",
    "calibrated_predicted_latency",
    "calibrated_latency_error",
    "true_status",
    "predicted_status"
]].to_string(index=False))
