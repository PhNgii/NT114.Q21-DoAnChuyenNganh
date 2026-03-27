import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_PATH = "data/qos_dataset.csv"
MODEL_PATH = "models/latency_model.pkl"
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

TARGET = "latency"

def main():
    df = pd.read_csv(DATA_PATH)

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        random_state=42
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    r2 = r2_score(y_test, y_pred)

    print("=== Latency Regression Results ===")
    print(f"MAE  : {mae:.4f}")
    print(f"RMSE : {rmse:.4f}")
    print(f"R2   : {r2:.4f}")

    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to: {MODEL_PATH}")

    # Save prediction results
    results_df = pd.DataFrame({
        "Actual Latency": y_test.values,
        "Predicted Latency": y_pred
    })
    results_df.to_csv(f"{OUTPUT_DIR}/latency_predictions.csv", index=False)

    # Plot Actual vs Predicted
    plt.figure(figsize=(7, 6))
    plt.scatter(y_test, y_pred)
    plt.xlabel("Actual Latency")
    plt.ylabel("Predicted Latency")
    plt.title("Actual vs Predicted Latency")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/latency_actual_vs_predicted.png")
    plt.close()

    # Feature importance
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        "Feature": FEATURES,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False)

    importance_df.to_csv(f"{OUTPUT_DIR}/latency_feature_importance.csv", index=False)

    plt.figure(figsize=(9, 5))
    plt.bar(importance_df["Feature"], importance_df["Importance"])
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Feature")
    plt.ylabel("Importance")
    plt.title("Feature Importance for Latency Prediction")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/latency_feature_importance.png")
    plt.close()

if __name__ == "__main__":
    main()