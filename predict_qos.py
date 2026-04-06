import json
import sys
from pathlib import Path

import joblib
import pandas as pd

from recommender import generate_recommendations

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
LATENCY_MODEL_PATH = BASE_DIR / "models" / "latency_model.pkl"
STATUS_MODEL_PATH = BASE_DIR / "models" / "status_model.pkl"
ENCODER_PATH = BASE_DIR / "models" / "status_label_encoder.pkl"

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


def to_float(payload, key, default=0.0):
    value = payload.get(key, default)
    if value == "" or value is None:
        return float(default)
    return float(value)


def to_int(payload, key, default=0):
    value = payload.get(key, default)
    if value == "" or value is None:
        return int(default)
    return int(float(value))


def normalize_payload(payload):
    hour = to_int(payload, "time_of_day", 12)
    is_peak_default = 1 if 18 <= hour <= 22 else 0

    return {
        "cpu_usage": to_float(payload, "cpu_usage"),
        "memory_usage": to_float(payload, "memory_usage"),
        "bandwidth_usage": to_float(payload, "bandwidth_usage"),
        "packet_loss": to_float(payload, "packet_loss"),
        "network_load": to_float(payload, "network_load"),
        "active_users": to_int(payload, "active_users"),
        "request_rate": to_float(payload, "request_rate"),
        "instance_count": to_int(payload, "instance_count", 1),
        "time_of_day": hour,
        "is_peak_hour": to_int(payload, "is_peak_hour", is_peak_default),
    }


def main():
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            raise ValueError("No input JSON received.")

        payload = json.loads(raw)
        sample = normalize_payload(payload)

        latency_model = joblib.load(LATENCY_MODEL_PATH)
        status_model = joblib.load(STATUS_MODEL_PATH)
        encoder = joblib.load(ENCODER_PATH)

        X_input = pd.DataFrame([sample])[FEATURES]

        predicted_latency = float(latency_model.predict(X_input)[0])
        predicted_status_encoded = status_model.predict(X_input)[0]
        predicted_status = str(
            encoder.inverse_transform([predicted_status_encoded])[0]
        )

        recommendations = generate_recommendations(
            input_data=sample,
            predicted_latency=predicted_latency,
            predicted_status=predicted_status,
        )

        result = {
            "predicted_latency": round(predicted_latency, 2),
            "predicted_status": predicted_status,
            "recommendations": recommendations,
            "model_input": sample,
        }

        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()