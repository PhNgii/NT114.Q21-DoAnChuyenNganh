import joblib
import pandas as pd

from recommender import generate_recommendations

LATENCY_MODEL_PATH = "models/latency_model.pkl"
STATUS_MODEL_PATH = "models/status_model.pkl"
ENCODER_PATH = "models/status_label_encoder.pkl"

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

def main():
    latency_model = joblib.load(LATENCY_MODEL_PATH)
    status_model = joblib.load(STATUS_MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)

    # sample input
    sample = {
        "cpu_usage": 92.0,
        "memory_usage": 88.0,
        "bandwidth_usage": 95.0,
        "packet_loss": 4.2,
        "network_load": 91.0,
        "active_users": 850,
        "request_rate": 1800.0,
        "instance_count": 2,
        "time_of_day": 19,
        "is_peak_hour": 1,
    }

    X_input = pd.DataFrame([sample])[FEATURES]

    predicted_latency = latency_model.predict(X_input)[0]
    predicted_status_encoded = status_model.predict(X_input)[0]
    predicted_status = encoder.inverse_transform([predicted_status_encoded])[0]

    recommendations = generate_recommendations(
        input_data=sample,
        predicted_latency=predicted_latency,
        predicted_status=predicted_status
    )

    print("=== Input ===")
    print(sample)

    print("\n=== Predictions ===")
    print(f"Predicted Latency: {predicted_latency:.2f} ms")
    print(f"Predicted QoS Status: {predicted_status}")

    print("\n=== Recommendations ===")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

if __name__ == "__main__":
    main()