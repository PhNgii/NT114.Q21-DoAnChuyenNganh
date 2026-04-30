import csv
import json
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AWS_METRICS_ENDPOINT = "http://localhost:3000/api/aws/ec2-metrics"
TARGET_URL = "http://13.236.94.75:3000/"

OUTPUT_DIR = Path("eval")
OUTPUT_DIR.mkdir(exist_ok=True)

FEATURE_KEYS = [
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


def get_json(url):
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def measure_actual_latency_ms(url):
    start = time.perf_counter()
    with urllib.request.urlopen(url, timeout=15) as response:
        response.read()
    end = time.perf_counter()
    return (end - start) * 1000


def run_model(features):
    process = subprocess.run(
        ["./.venv/bin/python", "predict_qos.py"],
        input=json.dumps(features),
        text=True,
        capture_output=True,
        timeout=30,
    )

    if process.returncode != 0:
        raise RuntimeError(process.stderr or process.stdout)

    result = json.loads(process.stdout)

    if "error" in result:
        raise RuntimeError(result["error"])

    return result


def make_true_status(actual_latency, packet_loss):
    """
    Rule-based label theo SLA demo.
    Có thể chỉnh ngưỡng theo báo cáo của nhóm.
    """
    if actual_latency >= 150 or packet_loss >= 2.0:
        return "Critical"

    if actual_latency >= 80 or packet_loss >= 1.0:
        return "Warning"

    return "Good"


def collect(samples=30, interval=60):
    output_file = OUTPUT_DIR / f"aws_eval_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    fields = [
        "timestamp",
        *FEATURE_KEYS,
        "actual_latency",
        "predicted_latency",
        "latency_error",
        "true_status",
        "predicted_status",
        "status_correct",
        "recommendations",
        "raw_cpu",
        "raw_memory",
        "raw_net_sent",
        "raw_net_recv",
    ]

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for i in range(samples):
            try:
                aws_response = get_json(AWS_METRICS_ENDPOINT)
                aws_metrics = aws_response["metrics"]
                raw = aws_metrics.get("raw", {})

                now = datetime.now()
                hour = now.hour

                features = {
                    "cpu_usage": aws_metrics["cpu_usage"],
                    "memory_usage": aws_metrics["memory_usage"],
                    "bandwidth_usage": aws_metrics["bandwidth_usage"],
                    "packet_loss": aws_metrics["packet_loss"],
                    "network_load": aws_metrics["network_load"],
                    "active_users": aws_metrics["active_users"],
                    "request_rate": aws_metrics["request_rate"],
                    "instance_count": aws_metrics["instance_count"],
                    "time_of_day": hour,
                    "is_peak_hour": 1 if 18 <= hour <= 22 else 0,
                }

                actual_latency = measure_actual_latency_ms(TARGET_URL)
                prediction = run_model(features)

                predicted_latency = float(prediction["predicted_latency"])
                predicted_status = prediction["predicted_status"]
                true_status = make_true_status(actual_latency, features["packet_loss"])

                row = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **features,
                    "actual_latency": round(actual_latency, 2),
                    "predicted_latency": round(predicted_latency, 2),
                    "latency_error": round(abs(actual_latency - predicted_latency), 2),
                    "true_status": true_status,
                    "predicted_status": predicted_status,
                    "status_correct": true_status == predicted_status,
                    "recommendations": " | ".join(prediction.get("recommendations", [])),
                    "raw_cpu": raw.get("cpu"),
                    "raw_memory": raw.get("memory"),
                    "raw_net_sent": raw.get("netSent"),
                    "raw_net_recv": raw.get("netRecv"),
                }

                writer.writerow(row)
                file.flush()

                print(
                    f"[{i + 1}/{samples}] "
                    f"actual={row['actual_latency']}ms, "
                    f"pred={row['predicted_latency']}ms, "
                    f"true={row['true_status']}, "
                    f"pred_status={row['predicted_status']}, "
                    f"correct={row['status_correct']}"
                )

            except Exception as error:
                print(f"[{i + 1}/{samples}] ERROR: {error}")

            if i < samples - 1:
                time.sleep(interval)

    print(f"\nSaved: {output_file}")


if __name__ == "__main__":
    import sys

    samples = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    collect(samples=samples, interval=interval)
