require('dotenv').config();

const fs = require('fs/promises');
const path = require('path');
const { spawn } = require('child_process');
const express = require('express');
const { getEc2QoSMetrics } = require('./cloudwatchMetrics');

const app = express();

const PORT = process.env.PORT || 3000;
const DATA_DIR = path.join(__dirname, 'data');
const DATA_FILE = path.join(DATA_DIR, 'metrics.json');
const PREDICT_SCRIPT = path.join(__dirname, 'predict_qos.py');
const PUBLIC_DIR = path.join(__dirname, 'public');

const PYTHON_BIN =
  process.env.PYTHON_PATH ||
  (process.platform === 'win32' ? 'python' : 'python3');

app.use(express.json());
app.use(express.static(PUBLIC_DIR));

const defaultData = {
  metadata: {
    systemName: 'QoS Command Center',
    location: 'ap-southeast-2 • AWS EC2',
    uptimeValue: '99.97%',
    slaValue: '92%',
    riskLevel: 'Medium',
    lastOptimization: null,
    lastUpdated: new Date().toISOString()
  },
  series: {
    labels: ['10:00', '10:05', '10:10', '10:15', '10:20', '10:25', '10:30'],
    actualLatency: [40, 42, 48, 55, 52, 57, 52],
    predictedLatency: [45, 50, 60, 75, 78, 82, 79],
    throughputSeries: [132, 126, 121, 118, 116, 120, 118],
    packetLossSeries: [0.1, 0.1, 0.2, 0.3, 0.2, 0.3, 0.2]
  },
  recommendations: [
    {
      icon: '01',
      title: 'Re-route burst traffic',
      description: 'Move short-lived requests away from the busiest path to reduce queueing delay.'
    },
    {
      icon: '02',
      title: 'Scale network-intensive workers',
      description: 'Provision more capacity for throughput-heavy services during the predicted spike.'
    },
    {
      icon: '03',
      title: 'Prioritize latency-sensitive flows',
      description: 'Apply QoS rules to preserve response time for critical traffic classes.'
    }
  ],
  insights: [
    {
      icon: 'AI',
      title: 'Prediction confidence remains high',
      description: 'The model found a consistent upward trend after 10:10, likely caused by burst traffic accumulation.'
    },
    {
      icon: 'ML',
      title: 'Best intervention window is now',
      description: 'Applying routing and scaling before the next spike should protect the SLA and reduce expected delay.'
    },
    {
      icon: 'QoS',
      title: 'Critical flows should be prioritized',
      description: 'Latency-sensitive service classes can be preserved by using policy-based queue prioritization.'
    }
  ],
  alertText:
    'The model detects a rising latency slope. Consider optimization before SLA risk crosses the warning threshold.'
};

async function ensureDataFile() {
  await fs.mkdir(DATA_DIR, { recursive: true });

  try {
    await fs.access(DATA_FILE);
  } catch {
    await fs.writeFile(DATA_FILE, JSON.stringify(defaultData, null, 2), 'utf8');
  }
}

async function readData() {
  await ensureDataFile();

  try {
    const raw = await fs.readFile(DATA_FILE, 'utf8');
    return JSON.parse(raw);
  } catch (error) {
    console.error('Failed to read metrics.json:', error);
    return JSON.parse(JSON.stringify(defaultData));
  }
}

async function writeData(data) {
  try {
    data.metadata.lastUpdated = new Date().toISOString();
    await fs.writeFile(DATA_FILE, JSON.stringify(data, null, 2), 'utf8');
  } catch (error) {
    console.error('Failed to write metrics.json:', error);
    throw error;
  }
}

function clampSeries(data, limit = 12) {
  const keys = [
    'labels',
    'actualLatency',
    'predictedLatency',
    'throughputSeries',
    'packetLossSeries'
  ];

  for (const key of keys) {
    if (Array.isArray(data.series[key]) && data.series[key].length > limit) {
      data.series[key] = data.series[key].slice(-limit);
    }
  }

  return data;
}

function formatNextLabel() {
  return new Date().toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit'
  });
}

function toRecommendationItems(texts = []) {
  return texts.map((text, index) => ({
    icon: String(index + 1).padStart(2, '0'),
    title: `AI Recommendation ${index + 1}`,
    description: text
  }));
}

function isInRange(value, min, max) {
  return (
    typeof value === 'number' &&
    !Number.isNaN(value) &&
    value >= min &&
    value <= max
  );
}

function buildAlert(predictedStatus, predictedLatency, actualLatency) {
  const diff = predictedLatency - actualLatency;

  if (predictedStatus === 'Critical') {
    return `AI predicts Critical status with latency ${predictedLatency.toFixed(2)} ms. Immediate optimization is recommended.`;
  }

  if (predictedStatus === 'Warning') {
    if (diff > 0) {
      return `AI predicts rising latency in the next cycle (${predictedLatency.toFixed(2)} ms), about ${diff.toFixed(2)} ms higher than current actual latency ${actualLatency} ms.`;
    }

    return `AI predicts a warning trend. Predicted latency is ${predictedLatency.toFixed(2)} ms while current actual latency is ${actualLatency} ms.`;
  }

  return `AI predicts the system is stable. Current predicted latency is ${predictedLatency.toFixed(2)} ms.`;
}

function mapStatusToRiskLevel(status) {
  if (status === 'Critical') return 'High';
  if (status === 'Warning') return 'Medium';
  return 'Low';
}

function runPythonPrediction(payload) {
  return new Promise((resolve, reject) => {
    const py = spawn(PYTHON_BIN, [PREDICT_SCRIPT], {
      cwd: __dirname,
      env: {
        ...process.env,
        PYTHONIOENCODING: 'utf-8'
      }
    });

    py.on('error', (err) => {
      reject(new Error(`Cannot start Python process: ${err.message}`));
    });

    let stdout = '';
    let stderr = '';

    py.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });

    py.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    py.on('close', (code) => {
      if (code !== 0) {
        return reject(new Error(stderr || stdout || 'Python prediction failed'));
      }

      try {
        const result = JSON.parse(stdout);

        if (result.error) {
          return reject(new Error(result.error));
        }

        resolve(result);
      } catch (err) {
        reject(new Error(`Cannot parse JSON from Python: ${stdout}`));
      }
    });

    py.stdin.write(JSON.stringify(payload));
    py.stdin.end();
  });
}

function computeScores(data) {
  const latestActual = data.series.actualLatency.at(-1) ?? 0;
  const latestPredicted = data.series.predictedLatency.at(-1) ?? 0;
  const latestThroughput = data.series.throughputSeries.at(-1) ?? 0;
  const latestPacketLoss = data.series.packetLossSeries.at(-1) ?? 0;

  const latencyScore = Math.max(68, Math.min(98, 100 - latestActual * 0.32));
  const throughputScore = Math.max(70, Math.min(98, latestThroughput * 0.75));
  const reliabilityScore = Math.max(65, Math.min(99, 98 - latestPacketLoss * 20));
  const aiScore = Math.max(
    75,
    Math.min(97, 100 - Math.abs(latestPredicted - latestActual) * 0.55)
  );

  return {
    latestActual,
    latestPredicted,
    latestThroughput,
    latestPacketLoss,
    latencyScore: Math.round(latencyScore),
    throughputScore: Math.round(throughputScore),
    reliabilityScore: Math.round(reliabilityScore),
    aiScore: Math.round(aiScore),
    impactValue: `+${Math.max(0, latestPredicted - latestActual)} ms`
  };
}

function createResponse(data) {
  return {
    ...data,
    computed: computeScores(data),
    optimizationPreview: data.optimizationPreview || null
  };
}

function buildOptimizationPreview(before, after) {
  return {
    before: {
      latency: before.latency,
      throughput: before.throughput,
      packetLoss: before.packetLoss
    },
    after: {
      latency: after.latency,
      throughput: after.throughput,
      packetLoss: after.packetLoss
    }
  };
}

async function applyPredictionToDashboard({
  label,
  actualLatency,
  throughput,
  packetLoss,
  prediction,
  source = 'Manual input'
}) {
  const data = await readData();

  data.series.labels.push(label || formatNextLabel());
  data.series.actualLatency.push(actualLatency);
  data.series.predictedLatency.push(Math.round(prediction.predicted_latency));
  data.series.throughputSeries.push(throughput);
  data.series.packetLossSeries.push(packetLoss);

  data.metadata.riskLevel = mapStatusToRiskLevel(prediction.predicted_status);
  data.alertText = buildAlert(
    prediction.predicted_status,
    prediction.predicted_latency,
    actualLatency
  );

  data.recommendations = toRecommendationItems(prediction.recommendations);

  data.latestPrediction = {
    source,
    actual_latency: actualLatency,
    throughput,
    packet_loss: packetLoss,
    predicted_latency: prediction.predicted_latency,
    predicted_status: prediction.predicted_status,
    model_input: prediction.model_input,
    recommendations: prediction.recommendations
  };

  clampSeries(data);
  await writeData(data);

  return data;
}

app.get('/api/dashboard-data', async (req, res) => {
  const data = await readData();
  res.json(createResponse(data));
});

app.get('/api/aws/ec2-metrics', async (req, res) => {
  try {
    const metrics = await getEc2QoSMetrics();

    res.json({
      ok: true,
      source: 'AWS CloudWatch',
      metrics
    });
  } catch (error) {
    console.error('CloudWatch metrics error:', error);
    res.status(500).json({
      ok: false,
      error: error.message || 'Cannot fetch AWS CloudWatch metrics.'
    });
  }
});

app.post('/api/aws/predict-from-cloudwatch', async (req, res) => {
  try {
    const awsMetrics = await getEc2QoSMetrics();
    const currentHour = new Date().getHours();

    const features = {
      cpu_usage: awsMetrics.cpu_usage,
      memory_usage: awsMetrics.memory_usage,
      bandwidth_usage: awsMetrics.bandwidth_usage,
      packet_loss: awsMetrics.packet_loss,
      network_load: awsMetrics.network_load,
      active_users: awsMetrics.active_users,
      request_rate: awsMetrics.request_rate,
      instance_count: awsMetrics.instance_count,
      time_of_day: currentHour,
      is_peak_hour: currentHour >= 18 && currentHour <= 22 ? 1 : 0
    };

    const prediction = await runPythonPrediction(features);

    const actualLatency =
      Number(req.body?.actualLatency) ||
      Math.max(40, Math.round(prediction.predicted_latency - 8));

    const throughput =
      Number(req.body?.throughput) ||
      Math.max(60, Math.round(150 - awsMetrics.network_load));

    const packetLoss = Number(req.body?.packetLoss) || awsMetrics.packet_loss;

    const data = await applyPredictionToDashboard({
      label: req.body?.label || 'AWS',
      actualLatency,
      throughput,
      packetLoss,
      prediction,
      source: 'AWS CloudWatch'
    });

    res.json({
      ok: true,
      source: 'AWS CloudWatch + AI Model',
      awsMetrics,
      prediction,
      dashboard: createResponse(data)
    });
  } catch (error) {
    console.error('AWS predict error:', error);
    res.status(500).json({
      ok: false,
      error: error.message || 'Cannot run AWS CloudWatch prediction.'
    });
  }
});

app.post('/api/metrics/manual', async (req, res) => {
  const { actualLatency, predictedLatency, throughput, packetLoss, label } = req.body || {};

  const values = {
    actualLatency: Number(actualLatency),
    predictedLatency: Number(predictedLatency),
    throughput: Number(throughput),
    packetLoss: Number(packetLoss)
  };

  const hasInvalidValue = Object.values(values).some((value) => Number.isNaN(value));

  if (hasInvalidValue) {
    return res.status(400).json({
      error: 'Dữ liệu không hợp lệ. Vui lòng nhập đủ 4 chỉ số.'
    });
  }

  const data = await readData();

  data.series.labels.push((label || '').trim() || formatNextLabel());
  data.series.actualLatency.push(values.actualLatency);
  data.series.predictedLatency.push(values.predictedLatency);
  data.series.throughputSeries.push(values.throughput);
  data.series.packetLossSeries.push(values.packetLoss);

  data.metadata.riskLevel =
    values.predictedLatency - values.actualLatency >= 20 ? 'High' : 'Medium';

  data.alertText =
    values.predictedLatency > values.actualLatency
      ? 'A new sample indicates predicted latency is higher than actual latency. Consider proactive optimization.'
      : 'The newest sample looks stable. Continue monitoring before scaling further.';

  clampSeries(data);
  await writeData(data);

  res.json(createResponse(data));
});

app.post('/api/metrics/simulate', async (req, res) => {
  try {
    const data = await readData();

    const lastActual = data.series.actualLatency.at(-1) ?? 50;
    const lastPredicted = data.series.predictedLatency.at(-1) ?? 60;
    const lastThroughput = data.series.throughputSeries.at(-1) ?? 120;
    const lastPacketLoss = data.series.packetLossSeries.at(-1) ?? 0.2;

    const actualLatency = Math.max(
      30,
      Math.min(120, lastActual + Math.round((Math.random() - 0.2) * 12))
    );

    const predictedLatency = Math.max(
      actualLatency,
      Math.min(140, lastPredicted + Math.round((Math.random() + 0.1) * 14))
    );

    const throughput = Math.max(
      80,
      Math.min(180, lastThroughput + Math.round((Math.random() - 0.45) * 14))
    );

    const packetLoss = Math.max(
      0.0,
      Math.min(2.5, Number((lastPacketLoss + (Math.random() - 0.5) * 0.25).toFixed(1)))
    );

    data.series.labels.push(formatNextLabel());
    data.series.actualLatency.push(actualLatency);
    data.series.predictedLatency.push(predictedLatency);
    data.series.throughputSeries.push(throughput);
    data.series.packetLossSeries.push(packetLoss);

    data.metadata.riskLevel =
      predictedLatency - actualLatency >= 25
        ? 'High'
        : predictedLatency - actualLatency >= 12
        ? 'Medium'
        : 'Low';

    data.alertText =
      data.metadata.riskLevel === 'High'
        ? 'The simulated sample shows a sharp rise in predicted latency. Immediate mitigation is recommended.'
        : 'The simulated sample was added successfully. Monitoring remains active.';

    clampSeries(data);
    await writeData(data);

    res.json(createResponse(data));
  } catch (error) {
    console.error('Simulate error:', error);
    res.status(500).json({
      error: error.message || 'Failed to simulate metrics.'
    });
  }
});

app.post('/api/metrics/predict', async (req, res) => {
  try {
    const actualLatency = Number(req.body.actualLatency);
    const throughput = Number(req.body.throughput);
    const packetLoss = Number(req.body.packetLoss);

    if ([actualLatency, throughput, packetLoss].some((v) => Number.isNaN(v))) {
      return res.status(400).json({
        error: 'Missing actualLatency, throughput or packetLoss.'
      });
    }

    const currentHour = new Date().getHours();

    const features = {
      cpu_usage: Number(req.body.cpuUsage),
      memory_usage: Number(req.body.memoryUsage),
      bandwidth_usage: Number(req.body.bandwidthUsage),
      packet_loss: packetLoss,
      network_load: Number(req.body.networkLoad),
      active_users: Number(req.body.activeUsers),
      request_rate: Number(req.body.requestRate),
      instance_count: Number(req.body.instanceCount),
      time_of_day:
        req.body.timeOfDay !== undefined && req.body.timeOfDay !== ''
          ? Number(req.body.timeOfDay)
          : currentHour,
      is_peak_hour:
        req.body.isPeakHour !== undefined && req.body.isPeakHour !== ''
          ? Number(req.body.isPeakHour)
          : currentHour >= 18 && currentHour <= 22
          ? 1
          : 0
    };

    const invalidFeature = Object.values(features).some((v) => Number.isNaN(v));

    if (invalidFeature) {
      return res.status(400).json({
        error: 'Missing model features for AI prediction.'
      });
    }

    if (
      !isInRange(features.cpu_usage, 0, 100) ||
      !isInRange(features.memory_usage, 0, 100) ||
      !isInRange(features.bandwidth_usage, 0, 100) ||
      !isInRange(features.packet_loss, 0, 100) ||
      !isInRange(features.network_load, 0, 100) ||
      !isInRange(features.time_of_day, 0, 23) ||
      !isInRange(features.is_peak_hour, 0, 1) ||
      actualLatency < 0 ||
      throughput < 0 ||
      features.active_users < 0 ||
      features.request_rate < 0 ||
      features.instance_count < 1
    ) {
      return res.status(400).json({
        error: 'Input values are out of valid range.'
      });
    }

    const prediction = await runPythonPrediction(features);

    const data = await applyPredictionToDashboard({
      label: (req.body.label || '').trim() || formatNextLabel(),
      actualLatency,
      throughput,
      packetLoss,
      prediction,
      source: 'Manual AI input'
    });

    res.json(createResponse(data));
  } catch (error) {
    console.error('Prediction error:', error);
    res.status(500).json({
      error: error.message || 'Cannot run AI prediction.'
    });
  }
});

function buildScenarioResult(type, data) {
  const i = data.series.actualLatency.length - 1;

  const current = {
    latency: data.series.actualLatency[i] ?? 50,
    predictedLatency: data.series.predictedLatency[i] ?? 70,
    throughput: data.series.throughputSeries[i] ?? 118,
    packetLoss: data.series.packetLossSeries[i] ?? 0.2
  };

  switch (type) {
    case 'peak':
      return {
        scenario: 'peak',
        estimatedLatency: current.predictedLatency + 12,
        estimatedRisk: 'High',
        suggestedAction: 'Scale out before burst traffic'
      };

    case 'congestion':
      return {
        scenario: 'congestion',
        estimatedLatency: current.predictedLatency + 18,
        estimatedRisk: 'High',
        suggestedAction: 'Re-route traffic and apply traffic shaping'
      };

    case 'loss':
      return {
        scenario: 'loss',
        estimatedLatency: current.predictedLatency + 8,
        estimatedRisk: 'Medium',
        suggestedAction: 'Inspect network path and reduce packet loss'
      };

    case 'scaleout':
      return {
        scenario: 'scaleout',
        estimatedLatency: Math.max(current.latency, current.predictedLatency - 10),
        estimatedRisk: 'Low',
        suggestedAction: 'Scale out preview shows improvement'
      };

    case 'normal':
    default:
      return {
        scenario: 'normal',
        estimatedLatency: current.predictedLatency,
        estimatedRisk: 'Medium',
        suggestedAction: 'Scale before burst'
      };
  }
}

app.post('/api/optimize', async (req, res) => {
  const data = await readData();

  const i = data.series.actualLatency.length - 1;

  if (i >= 0) {
    const before = {
      latency: data.series.predictedLatency[i],
      throughput: data.series.throughputSeries[i],
      packetLoss: data.series.packetLossSeries[i]
    };

    const after = {
      latency: Math.max(data.series.actualLatency[i], data.series.predictedLatency[i] - 8),
      throughput: data.series.throughputSeries[i] + 6,
      packetLoss: Math.max(0, Number((data.series.packetLossSeries[i] - 0.1).toFixed(1)))
    };

    data.optimizationPreview = buildOptimizationPreview(before, after);

    data.series.predictedLatency[i] = after.latency;
    data.series.packetLossSeries[i] = after.packetLoss;
    data.series.throughputSeries[i] = after.throughput;
  }

  data.metadata.slaValue = '96%';
  data.metadata.riskLevel = 'Lower';
  data.metadata.lastOptimization = new Date().toISOString();

  data.alertText =
    'Recommendation preview generated. The dashboard shows expected QoS improvement if the suggested actions are applied.';

  data.recommendations = [
    {
      icon: 'AI',
      title: 'Scale before the next burst window',
      description: 'Provision additional workers a few minutes before the predicted spike to protect SLA.'
    },
    {
      icon: 'NET',
      title: 'Apply traffic shaping for noisy flows',
      description: 'Limit non-critical traffic so latency-sensitive requests keep lower delay.'
    },
    {
      icon: 'OPS',
      title: 'Keep anomaly watch active',
      description: 'Continue collecting samples to validate whether the optimization reduces the next peak.'
    }
  ];

  await writeData(data);
  res.json(createResponse(data));
});

app.post('/api/inspect', async (req, res) => {
  const data = await readData();
  data.recommendations = data.insights;
  await writeData(data);
  res.json(createResponse(data));
});

app.post('/api/reset', async (req, res) => {
  await writeData(JSON.parse(JSON.stringify(defaultData)));
  const data = await readData();
  res.json(createResponse(data));
});

app.get('/', (req, res) => {
  res.sendFile(path.join(PUBLIC_DIR, 'index.html'));
});

app.post('/api/scenario', async (req, res) => {
  const data = await readData();
  const { scenario } = req.body || {};

  const result = buildScenarioResult(scenario, data);

  res.json({
    ok: true,
    scenarioResult: result
  });
});
process.on('uncaughtException', (err) => {
  console.error('UNCAUGHT EXCEPTION:', err);
});

process.on('unhandledRejection', (reason) => {
  console.error('UNHANDLED REJECTION:', reason);
});

process.on('exit', (code) => {
  console.log('PROCESS EXIT with code:', code);
});

async function startServer() {
  try {
    console.log('Starting server...');
    console.log('Current working directory:', process.cwd());
    console.log('Server file directory:', __dirname);
    console.log('PORT =', PORT);
    console.log('PYTHON_BIN =', PYTHON_BIN);
    console.log('DATA_FILE =', DATA_FILE);
    console.log('AWS_REGION =', process.env.AWS_REGION);
    console.log('EC2_INSTANCE_ID =', process.env.EC2_INSTANCE_ID);

    await ensureDataFile();
    console.log('Data file is ready.');

    const server = app.listen(PORT, () => {
      console.log(`Server running at http://localhost:${PORT}`);
      console.log('PID =', process.pid);
    });

    server.on('error', (err) => {
      console.error('SERVER ERROR:', err);
    });

    server.on('close', () => {
      console.log('SERVER CLOSED');
    });
  } catch (error) {
    console.error('STARTUP FAILED:', error);
  }
}

startServer();
