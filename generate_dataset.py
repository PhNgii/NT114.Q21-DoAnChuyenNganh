import os
import numpy as np
import pandas as pd

np.random.seed(42)

NUM_SAMPLES = 5000
OUTPUT_PATH = "data/qos_dataset.csv"

os.makedirs("data", exist_ok=True)

def generate_sample():
    scenario = np.random.choice(
        ["normal", "high_load", "failure"],
        p=[0.35, 0.40, 0.25]
    )

    if scenario == "normal":
        cpu_usage = np.random.uniform(10, 55)
        memory_usage = np.random.uniform(20, 60)
        bandwidth_usage = np.random.uniform(10, 55)
        packet_loss = np.random.uniform(0, 1.0)
        network_load = np.random.uniform(10, 50)
        active_users = np.random.randint(20, 300)
        request_rate = np.random.uniform(50, 700)
        instance_count = np.random.randint(3, 8)

    elif scenario == "high_load":
        cpu_usage = np.random.uniform(55, 85)
        memory_usage = np.random.uniform(50, 85)
        bandwidth_usage = np.random.uniform(50, 85)
        packet_loss = np.random.uniform(0.5, 2.5)
        network_load = np.random.uniform(45, 85)
        active_users = np.random.randint(250, 700)
        request_rate = np.random.uniform(600, 1500)
        instance_count = np.random.randint(2, 6)

    else:  # failure
        cpu_usage = np.random.uniform(80, 100)
        memory_usage = np.random.uniform(75, 100)
        bandwidth_usage = np.random.uniform(80, 100)
        packet_loss = np.random.uniform(2.5, 5.0)
        network_load = np.random.uniform(80, 100)
        active_users = np.random.randint(600, 1000)
        request_rate = np.random.uniform(1400, 2000)
        instance_count = np.random.randint(1, 4)

    time_of_day = np.random.randint(0, 24)
    is_peak_hour = 1 if time_of_day in [8, 9, 10, 11, 18, 19, 20, 21] else 0

    latency = (
        8
        + 0.35 * cpu_usage
        + 0.20 * memory_usage
        + 0.25 * bandwidth_usage
        + 10.0 * packet_loss
        + 0.30 * network_load
        + 0.010 * active_users
        + 0.008 * request_rate
        - 4.0 * instance_count
        + 8 * is_peak_hour
        + np.random.normal(0, 5)
    )

    jitter = (
        1
        + 0.08 * bandwidth_usage
        + 0.12 * network_load
        + 5.0 * packet_loss
        + 0.003 * active_users
        + 3 * is_peak_hour
        + np.random.normal(0, 2)
    )

    throughput = (
        130
        - 0.25 * bandwidth_usage
        - 0.20 * network_load
        - 7.0 * packet_loss
        - 0.12 * latency
        + 3.0 * instance_count
        + np.random.normal(0, 5)
    )

    latency = max(latency, 1)
    jitter = max(jitter, 0)
    throughput = max(throughput, 1)

    if latency < 80 and jitter < 20 and throughput > 70:
        qos_status = "Good"
    elif latency < 145 and jitter < 40 and throughput > 45:
        qos_status = "Warning"
    else:
        qos_status = "Critical"

    return {
        "cpu_usage": round(cpu_usage, 2),
        "memory_usage": round(memory_usage, 2),
        "bandwidth_usage": round(bandwidth_usage, 2),
        "packet_loss": round(packet_loss, 2),
        "network_load": round(network_load, 2),
        "active_users": active_users,
        "request_rate": round(request_rate, 2),
        "instance_count": instance_count,
        "time_of_day": time_of_day,
        "is_peak_hour": is_peak_hour,
        "latency": round(latency, 2),
        "jitter": round(jitter, 2),
        "throughput": round(throughput, 2),
        "qos_status": qos_status,
    }

def main():
    data = [generate_sample() for _ in range(NUM_SAMPLES)]
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved dataset to: {OUTPUT_PATH}")
    print(df.head())
    print("\nClass distribution:")
    print(df["qos_status"].value_counts())

if __name__ == "__main__":
    main()