import sys
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

if len(sys.argv) < 2:
    print("Usage: python3 scripts/evaluate_aws_eval_dataset.py eval/aws_eval_dataset_xxx.csv")
    sys.exit(1)

csv_path = sys.argv[1]
df = pd.read_csv(csv_path)

df = df.dropna(subset=["actual_latency", "predicted_latency", "true_status", "predicted_status"])

actual = df["actual_latency"].astype(float)
pred = df["predicted_latency"].astype(float)

errors = np.abs(actual - pred)

mae = mean_absolute_error(actual, pred)
rmse = mean_squared_error(actual, pred) ** 0.5

if len(df) >= 2:
    r2 = r2_score(actual, pred)
else:
    r2 = None

mape = np.mean(np.abs((actual - pred) / actual)) * 100
approx_accuracy = max(0, 100 - mape)

acc_5 = np.mean(errors <= 5) * 100
acc_10 = np.mean(errors <= 10) * 100
acc_20 = np.mean(errors <= 20) * 100
acc_30 = np.mean(errors <= 30) * 100

status_acc = accuracy_score(df["true_status"], df["predicted_status"]) * 100

print("========== AWS EVALUATION RESULT ==========")
print(f"File: {csv_path}")
print(f"Samples: {len(df)}")
print()
print("Latency Regression:")
print(f"MAE: {mae:.2f} ms")
print(f"RMSE: {rmse:.2f} ms")
print(f"MAPE: {mape:.2f}%")
print(f"Approx Accuracy: {approx_accuracy:.2f}%")
if r2 is not None:
    print(f"R2 Score: {r2:.4f}")

print()
print("Tolerance Accuracy:")
print(f"Within ±5 ms : {acc_5:.2f}%")
print(f"Within ±10 ms: {acc_10:.2f}%")
print(f"Within ±20 ms: {acc_20:.2f}%")
print(f"Within ±30 ms: {acc_30:.2f}%")

print()
print("Status Classification:")
print(f"Status Accuracy: {status_acc:.2f}%")
print()
print(classification_report(df["true_status"], df["predicted_status"], zero_division=0))

labels = ["Good", "Warning", "Critical"]
print("Confusion Matrix:")
print(confusion_matrix(df["true_status"], df["predicted_status"], labels=labels))

print()
print("Label Distribution:")
print(df["true_status"].value_counts())

print()
print("Prediction Distribution:")
print(df["predicted_status"].value_counts())
