from recommender import generate_recommendations

def main():
    scenarios = [
        {
            "name": "Normal Load",
            "input": {
                "cpu_usage": 40,
                "memory_usage": 50,
                "bandwidth_usage": 45,
                "packet_loss": 0.5,
                "network_load": 40,
                "instance_count": 4,
                "is_peak_hour": 0
            },
            "predicted_latency": 55,
            "predicted_status": "Good"
        },
        {
            "name": "High CPU",
            "input": {
                "cpu_usage": 92,
                "memory_usage": 65,
                "bandwidth_usage": 70,
                "packet_loss": 1.2,
                "network_load": 75,
                "instance_count": 2,
                "is_peak_hour": 0
            },
            "predicted_latency": 160,
            "predicted_status": "Warning"
        },
        {
            "name": "High Packet Loss",
            "input": {
                "cpu_usage": 60,
                "memory_usage": 60,
                "bandwidth_usage": 80,
                "packet_loss": 4.5,
                "network_load": 78,
                "instance_count": 3,
                "is_peak_hour": 0
            },
            "predicted_latency": 175,
            "predicted_status": "Critical"
        },
        {
            "name": "Peak Hour Overload",
            "input": {
                "cpu_usage": 95,
                "memory_usage": 90,
                "bandwidth_usage": 96,
                "packet_loss": 3.8,
                "network_load": 94,
                "instance_count": 2,
                "is_peak_hour": 1
            },
            "predicted_latency": 220,
            "predicted_status": "Critical"
        }
    ]

    for scenario in scenarios:
        print("\n" + "=" * 60)
        print(f"Scenario: {scenario['name']}")
        recs = generate_recommendations(
            input_data=scenario["input"],
            predicted_latency=scenario["predicted_latency"],
            predicted_status=scenario["predicted_status"]
        )
        for i, rec in enumerate(recs, 1):
            print(f"{i}. {rec}")

if __name__ == "__main__":
    main()