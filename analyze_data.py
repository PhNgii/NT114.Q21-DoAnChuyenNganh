import os
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = "data/qos_dataset.csv"
OUTPUT_DIR = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    df = pd.read_csv(DATA_PATH)

    print("=== 5 dòng đầu ===")
    print(df.head())

    print("\n=== Thông tin dữ liệu ===")
    print(df.info())

    print("\n=== Thống kê mô tả ===")
    print(df.describe())

    print("\n=== Phân bố nhãn qos_status ===")
    print(df["qos_status"].value_counts())

    # 1. Histogram latency
    plt.figure(figsize=(8, 5))
    plt.hist(df["latency"], bins=30)
    plt.xlabel("Latency (ms)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Latency")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/latency_histogram.png")
    plt.close()

    # 2. Histogram jitter
    plt.figure(figsize=(8, 5))
    plt.hist(df["jitter"], bins=30)
    plt.xlabel("Jitter (ms)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Jitter")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/jitter_histogram.png")
    plt.close()

    # 3. Histogram throughput
    plt.figure(figsize=(8, 5))
    plt.hist(df["throughput"], bins=30)
    plt.xlabel("Throughput (Mbps)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Throughput")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/throughput_histogram.png")
    plt.close()

    # 4. Bar chart qos_status
    status_counts = df["qos_status"].value_counts()
    plt.figure(figsize=(7, 5))
    plt.bar(status_counts.index, status_counts.values)
    plt.xlabel("QoS Status")
    plt.ylabel("Count")
    plt.title("QoS Status Distribution")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/qos_status_distribution.png")
    plt.close()

    # 5. Correlation matrix
    numeric_df = df.select_dtypes(include=["int64", "float64"])
    corr = numeric_df.corr()

    plt.figure(figsize=(12, 8))
    plt.imshow(corr, aspect="auto")
    plt.colorbar()
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=90)
    plt.yticks(range(len(corr.columns)), corr.columns)
    plt.title("Correlation Matrix")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/correlation_matrix.png")
    plt.close()

    print("\nĐã lưu biểu đồ vào thư mục outputs/")

if __name__ == "__main__":
    main()