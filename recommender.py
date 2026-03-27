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
        recommendations.append("CPU usage cao: cân nhắc scale up hoặc scale out thêm instance.")

    if memory_usage > 85:
        recommendations.append("Memory usage cao: tăng RAM hoặc tối ưu ứng dụng để giảm tiêu thụ bộ nhớ.")

    if bandwidth_usage > 90:
        recommendations.append("Băng thông gần đầy: cân bằng tải hoặc nâng cấp giới hạn bandwidth.")

    if packet_loss > 3:
        recommendations.append("Packet loss cao: kiểm tra congestion, routing hoặc chất lượng đường truyền.")

    if network_load > 85:
        recommendations.append("Network load cao: phân phối lại workload hoặc bật auto scaling.")

    if predicted_latency > 150:
        recommendations.append("Latency dự đoán rất cao: ưu tiên mở rộng tài nguyên và kiểm tra bottleneck mạng.")

    if predicted_status == "Critical":
        recommendations.append("Trạng thái Critical: cần can thiệp ngay để tránh suy giảm QoS.")
    elif predicted_status == "Warning":
        recommendations.append("Trạng thái Warning: nên theo dõi sát và tối ưu sớm trước khi hệ thống quá tải.")

    if is_peak_hour == 1:
        recommendations.append("Đang trong giờ cao điểm: nên dùng auto scaling hoặc tăng số instance dự phòng.")

    if instance_count <= 2 and (cpu_usage > 80 or network_load > 80):
        recommendations.append("Số instance thấp so với tải hiện tại: nên tăng thêm instance.")

    if not recommendations:
        recommendations.append("Hệ thống đang ổn định, tiếp tục giám sát định kỳ.")

    return recommendations