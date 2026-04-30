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

def get_json(url):
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

def measure_http_latency_ms(url):
    start = time.perf_counter()
    with urllib.request.urlopen(url, timeout=15) as response:
        response.read()
    return (time.perf_counter() - start) * 1000

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

def apply_scenario(base, scenario):
    f = dict(base)

    if scenario == "normal":
        return f

    if scenario == "warning":
        f["cpu_usage"] = max(f["cpu_usage"], 72)
        f["memory_usage"] = max(f["memory_usage"], 78)
        f["bandwidth_usage"] = max(f["bandwidth_usage"], 6)
        f["network_load"] = max(f["network_load"], 65)
        f["packet_loss"] = max(f["packet_loss"], 1.2)
        f["active_users"] = max(f["active_users"], 850)
        f["request_rate"] = max(f["request_rate"], 1800)
        return f

    if scenario == "critical":
        f["cpu_usage"] = max(f["cpu_usage"], 92)
        f["memory_usage"] = max(f["memory_usage"], 90)
        f["bandwidth_usage"] = max(f["bandwidth_usage"], 9)
        f["network_load"] = max(f["network_load"], 92)
        f["packet_loss"] = max(f["packet_loss"], 3.5)
        f["active_users"] = max(f["active_users"], 2000)
        f["request_rate"] = max(f["request_rate"], 4500)
        return f

    raise ValueError(f"Unknown scenario: {scenario}")

def make_actual_latency(features, measured_http_latency):
    cpu = float(features.get("cpu_usage", 0) or 0)
    memory = float(features.get("memory_usage", 0) or 0)
    bandwidth = float(features.get("bandwidth_usage", 0) or 0)
    network_load = float(features.get("network_load", 0) or 0)
    packet_loss = float(features.get("packet_loss", 0) or 0)
    active_users = float(features.get("active_users", 0) or 0)
    request_rate = float(features.get("request_rate", 0) or 0)
    is_peak_hour = float(features.get("is_peak_hour", 0) or 0)

    latency = 20
    latency += cpu * 0.18
    latency += memory * 0.12
    latency += bandwidth * 0.8
    latency += network_load * 0.25
    latency += packet_loss * 12
    latency += active_users * 0.015
    latency += request_rate * 0.01
    latency += is_peak_hour * 8
    latency += min(float(measured_http_latency or 0), 50) * 0.2

    return round(latency, 2)

def make_true_status(actual_latency, packet_loss):
    if actual_latency >= 150 or packet_loss >= 2.0:
        return "Critical"

    if actual_latency >= 80 or packet_loss >= 1.0:
        return "Warning"

    return "Good"

def collect(samples_per_scenario=3, interval=5):
    output_file = OUTPUT_DIR / f"aws_scenario_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    fields = [
        "timestamp",
        "scenario",
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
        "measured_http_latency",
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

    scenarios = ["normal", "warning", "critical"]

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        total = samples_per_scenario * len(scenarios)
        count = 0

        for scenario in scenarios:
            for _ in range(samples_per_scenario):
                count += 1

                aws_response = get_json(AWS_METRICS_ENDPOINT)
                aws_metrics = aws_response["metrics"]
                raw = aws_metrics.get("raw", {})

                now = datetime.now()
                hour = now.hour

                base_features = {
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

                features = apply_scenario(base_features, scenario)

                measured_http_latency = measure_http_latency_ms(TARGET_URL)
                actual_latency = make_actual_latency(features, measured_http_latency)

                prediction = run_model(features)
                predicted_latency = float(prediction["predicted_latency"])
                predicted_status = prediction["predicted_status"]

                true_status = make_true_status(actual_latency, features["packet_loss"])

                row = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "scenario": scenario,
                    **features,
                    "measured_http_latency": round(measured_http_latency, 2),
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
                    f"[{count}/{total}] "
                    f"scenario={scenario}, "
                    f"actual={row['actual_latency']}ms, "
                    f"pred={row['predicted_latency']}ms, "
                    f"true={row['true_status']}, "
                    f"pred_status={row['predicted_status']}, "
                    f"correct={row['status_correct']}"
                )

                if count < total:
                    time.sleep(interval)

    print(f"\nSaved: {output_file}")

if __name__ == "__main__":
    import sys

    samples_per_scenario = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    collect(samples_per_scenario=samples_per_scenario, interval=interval)

