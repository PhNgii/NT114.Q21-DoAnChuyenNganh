def generate_recommendations(input_data, predicted_latency, predicted_status):
    recommendations = []

    cpu_usage = input_data["cpu_usage"]
    memory_usage = input_data["memory_usage"]
    bandwidth_usage = input_data["bandwidth_usage"]
    packet_loss = input_data["packet_loss"]
    network_load = input_data["network_load"]
    instance_count = input_data["instance_count"]
    is_peak_hour = input_data["is_peak_hour"]

    if cpu_usage > 85:
        recommendations.append("High CPU usage: consider scaling up or scaling out by adding more instances.")
    elif cpu_usage > 70:
        recommendations.append("CPU usage is increasing: monitor the system and prepare to expand resources if the load continues to rise.")

    if memory_usage > 85:
        recommendations.append("High memory usage: increase RAM or optimize the application to reduce memory consumption.")
    elif memory_usage > 70:
        recommendations.append("Memory usage is moderately high: check the application and consider reallocating resources.")

    if bandwidth_usage > 90:
        recommendations.append("Bandwidth is nearly saturated: apply load balancing or increase bandwidth capacity.")
    elif bandwidth_usage > 75:
        recommendations.append("Bandwidth usage is relatively high: continue monitoring to avoid congestion as traffic increases.")

    if packet_loss > 3:
        recommendations.append("High packet loss: check for congestion, routing issues, or link quality problems.")
    elif packet_loss > 1.5:
        recommendations.append("Packet loss is starting to increase: investigate early to prevent QoS degradation.")

    if network_load > 85:
        recommendations.append("High network load: redistribute workload or enable auto scaling.")
    elif network_load > 70:
        recommendations.append("Network load is moderately high: monitor closely to avoid overload during peak hours.")

    if predicted_latency > 150:
        recommendations.append("Predicted latency is very high: prioritize resource expansion and investigate network bottlenecks.")
    elif predicted_latency > 100:
        recommendations.append("Predicted latency is elevated: optimize the system early before it moves into a worse state.")

    if predicted_status == "Critical":
        recommendations.append("Critical status: immediate intervention is required to prevent QoS degradation.")
    elif predicted_status == "Warning":
        recommendations.append("Warning status: the system is not in severe failure yet, but signs of degradation are appearing and early optimization is needed.")
    elif predicted_status == "Good":
        recommendations.append("Good status: the system is stable, continue routine monitoring.")

    if is_peak_hour == 1:
        recommendations.append("Peak-hour condition detected: consider enabling auto scaling or increasing standby instances.")

    if instance_count <= 2 and (cpu_usage > 80 or network_load > 80):
        recommendations.append("The number of instances is too low for the current load: consider adding more instances.")

    return recommendations