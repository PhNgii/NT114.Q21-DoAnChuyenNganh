import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

DATA_PATH = "data/qos_dataset.csv"
MODEL_PATH = "models/status_model.pkl"
ENCODER_PATH = "models/status_label_encoder.pkl"
OUTPUT_DIR = "outputs"

os.makedirs("models", exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

TARGET = "qos_status"

def main():
    df = pd.read_csv(DATA_PATH)

    X = df[FEATURES]
    y = df[TARGET]

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        random_state=42
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)

    print("=== QoS Status Classification Results ===")
    print(f"Accuracy: {acc:.4f}")

    report = classification_report(y_test, y_pred, target_names=encoder.classes_)
    print("\nClassification Report:")
    print(report)

    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:")
    print(cm)

    # Save model and encoder
    joblib.dump(model, MODEL_PATH)
    joblib.dump(encoder, ENCODER_PATH)

    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved encoder to: {ENCODER_PATH}")

    # Save report
    with open(f"{OUTPUT_DIR}/classification_report.txt", "w", encoding="utf-8") as f:
        f.write(f"Accuracy: {acc:.4f}\n\n")
        f.write(report)

    # Save confusion matrix plot
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation="nearest")
    plt.title("Confusion Matrix")
    plt.colorbar()

    tick_marks = np.arange(len(encoder.classes_))
    plt.xticks(tick_marks, encoder.classes_, rotation=45)
    plt.yticks(tick_marks, encoder.classes_)

    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, str(cm[i, j]), ha="center", va="center")

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/confusion_matrix.png")
    plt.close()

    # Feature importance
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        "Feature": FEATURES,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False)

    importance_df.to_csv(f"{OUTPUT_DIR}/status_feature_importance.csv", index=False)

    plt.figure(figsize=(9, 5))
    plt.bar(importance_df["Feature"], importance_df["Importance"])
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Feature")
    plt.ylabel("Importance")
    plt.title("Feature Importance for QoS Status Classification")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/status_feature_importance.png")
    plt.close()

if __name__ == "__main__":
    main()