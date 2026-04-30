import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    classification_report,
    confusion_matrix
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import numpy as np

if len(sys.argv) < 2:
    print("Usage: ./.venv/bin/python scripts/train_from_aws_scenario.py eval/aws_scenario_eval_xxx.csv")
    sys.exit(1)

csv_path = sys.argv[1]
df = pd.read_csv(csv_path)

FEATURES = [
    "cpu_usage",
    "memory_usage",
    "bandwidth_usage",
    "packet_loss",
    "network_load",
    "active_users",
    "request_rate",
    "instance_count",
    "time_of_day",
    "is_peak_hour",
]

required = FEATURES + ["actual_latency", "true_status"]
df = df.dropna(subset=required).copy()

X = df[FEATURES]
y_latency = df["actual_latency"].astype(float)
y_status_text = df["true_status"].astype(str)

label_encoder = LabelEncoder()
y_status = label_encoder.fit_transform(y_status_text)

X_train, X_test, y_lat_train, y_lat_test, y_stat_train, y_stat_test = train_test_split(
    X,
    y_latency,
    y_status,
    test_size=0.25,
    random_state=42,
    stratify=y_status
)

latency_model = RandomForestRegressor(
    n_estimators=500,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    random_state=42,
    n_jobs=-1
)

status_model = RandomForestClassifier(
    n_estimators=500,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

latency_model.fit(X_train, y_lat_train)
status_model.fit(X_train, y_stat_train)

lat_pred = latency_model.predict(X_test)
stat_pred = status_model.predict(X_test)

mae = mean_absolute_error(y_lat_test, lat_pred)
rmse = mean_squared_error(y_lat_test, lat_pred) ** 0.5
mape = np.mean(np.abs((y_lat_test.values - lat_pred) / y_lat_test.values)) * 100
approx_accuracy = max(0, 100 - mape)
r2 = r2_score(y_lat_test, lat_pred)

status_acc = accuracy_score(y_stat_test, stat_pred) * 100

print("========== TRAIN FROM AWS SCENARIO RESULT ==========")
print(f"Dataset: {csv_path}")
print(f"Total samples: {len(df)}")
print(f"Train samples: {len(X_train)}")
print(f"Test samples : {len(X_test)}")
print()
print("Latency Regression:")
print(f"MAE: {mae:.2f} ms")
print(f"RMSE: {rmse:.2f} ms")
print(f"MAPE: {mape:.2f}%")
print(f"Approx Accuracy: {approx_accuracy:.2f}%")
print(f"R2 Score: {r2:.4f}")
print()
print("Status Classification:")
print(f"Accuracy: {status_acc:.2f}%")
print(classification_report(
    y_stat_test,
    stat_pred,
    target_names=label_encoder.classes_,
    zero_division=0
))
print("Confusion Matrix:")
print(confusion_matrix(y_stat_test, stat_pred))

Path("models").mkdir(exist_ok=True)

# Backup model cũ nếu có
for name in ["latency_model.pkl", "status_model.pkl", "label_encoder.pkl"]:
    p = Path("models") / name
    if p.exists():
        backup = Path("models") / (name + ".backup")
        p.replace(backup)
        print(f"Backup old model: {p} -> {backup}")

joblib.dump(latency_model, "models/latency_model.pkl")
joblib.dump(status_model, "models/status_model.pkl")
joblib.dump(label_encoder, "models/label_encoder.pkl")

print()
print("Saved new models:")
print("- models/latency_model.pkl")
print("- models/status_model.pkl")
print("- models/label_encoder.pkl")
