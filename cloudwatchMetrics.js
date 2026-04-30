require('dotenv').config();

const {
  CloudWatchClient,
  GetMetricDataCommand
} = require('@aws-sdk/client-cloudwatch');

const REGION = process.env.AWS_REGION || 'ap-southeast-2';

const INSTANCE_ID =
  process.env.EC2_INSTANCE_ID ||
  process.env.AWS_INSTANCE_ID;

const NETWORK_INTERFACE =
  process.env.AWS_NETWORK_INTERFACE || 'ens5';

const CUSTOM_NAMESPACE =
  process.env.AWS_METRIC_NAMESPACE || 'QoSApp/EC2';

const cloudwatch = new CloudWatchClient({ region: REGION });

function latestValue(result, id) {
  const item = result.MetricDataResults?.find((m) => m.Id === id);

  if (!item || !item.Values || item.Values.length === 0) {
    return null;
  }

  return Number(item.Values[0]);
}

async function getEc2QoSMetrics() {
  if (!INSTANCE_ID) {
    throw new Error(
      'Missing EC2_INSTANCE_ID or AWS_INSTANCE_ID in environment variables.'
    );
  }

  const end = new Date();
  const start = new Date(end.getTime() - 30 * 60 * 1000);

  const instanceDimensions = [
    {
      Name: 'InstanceId',
      Value: INSTANCE_ID
    }
  ];

  const networkDimensions = [
    {
      Name: 'InstanceId',
      Value: INSTANCE_ID
    },
    {
      Name: 'interface',
      Value: NETWORK_INTERFACE
    }
  ];

  const command = new GetMetricDataCommand({
    StartTime: start,
    EndTime: end,
    ScanBy: 'TimestampDescending',
    MetricDataQueries: [
      {
        Id: 'cpu',
        MetricStat: {
          Metric: {
            Namespace: 'AWS/EC2',
            MetricName: 'CPUUtilization',
            Dimensions: instanceDimensions
          },
          Period: 300,
          Stat: 'Average'
        },
        ReturnData: true
      },
      {
        Id: 'memory',
        MetricStat: {
          Metric: {
            Namespace: CUSTOM_NAMESPACE,
            MetricName: 'mem_used_percent',
            Dimensions: instanceDimensions
          },
          Period: 60,
          Stat: 'Average'
        },
        ReturnData: true
      },
      {
        Id: 'netSent',
        MetricStat: {
          Metric: {
            Namespace: CUSTOM_NAMESPACE,
            MetricName: 'net_bytes_sent',
            Dimensions: networkDimensions
          },
          Period: 60,
          Stat: 'Sum'
        },
        ReturnData: true
      },
      {
        Id: 'netRecv',
        MetricStat: {
          Metric: {
            Namespace: CUSTOM_NAMESPACE,
            MetricName: 'net_bytes_recv',
            Dimensions: networkDimensions
          },
          Period: 60,
          Stat: 'Sum'
        },
        ReturnData: true
      }
    ]
  });

  const result = await cloudwatch.send(command);

  const cpu = latestValue(result, 'cpu');
  const memory = latestValue(result, 'memory');
  const netSent = latestValue(result, 'netSent');
  const netRecv = latestValue(result, 'netRecv');

  const totalNetworkBytes = (netSent ?? 0) + (netRecv ?? 0);

  // Vì net_bytes_sent / net_bytes_recv đang lấy theo Period 60 giây,
  // bandwidthMbps = bytes * 8 / seconds / 1,000,000
  const bandwidthMbps = totalNetworkBytes > 0
    ? (totalNetworkBytes * 8) / 60 / 1000000
    : 0;

  // Network load là giá trị quy đổi tương đối 0-100 để đưa vào AI/dashboard.
  // Ở bản demo, giả sử 10 Mbps tương ứng 100% network load.
  const networkLoad = Math.min(100, (bandwidthMbps / 10) * 100);

  return {
    cpu_usage: Number((cpu ?? 0).toFixed(2)),
    memory_usage: Number((memory ?? 0).toFixed(2)),
    bandwidth_usage: Number(bandwidthMbps.toFixed(2)),
    network_load: Number(networkLoad.toFixed(2)),

    // Các field này hiện CloudWatch EC2 chưa có trực tiếp,
    // tạm dùng giá trị mô phỏng / bán thực tế cho demo AI.
    packet_loss: 0.2,
    active_users: 120,
    request_rate: 300,
    instance_count: 1,

    raw: {
      cpu,
      memory,
      netSent,
      netRecv,
      region: REGION,
      namespace: CUSTOM_NAMESPACE,
      instanceId: INSTANCE_ID,
      networkInterface: NETWORK_INTERFACE
    }
  };
}

module.exports = {
  getEc2QoSMetrics
};
