let chart;

const state = {
  data: null
};

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function setBar(id, value) {
  const bar = document.getElementById(id);
  if (bar) bar.style.width = `${value}%`;
}
function renderScenarioResult(result) {
  if (!result) return;

  setText('scenarioLatency', `${result.estimatedLatency} ms`);
  setText('scenarioRisk', result.estimatedRisk);
  setText('scenarioAction', result.suggestedAction);
}
function renderOptimizationPreview(preview) {
  if (!preview) {
    setText('beforeLatency', '--');
    setText('afterLatency', '--');
    setText('beforeThroughput', '--');
    setText('afterThroughput', '--');
    setText('beforePacketLoss', '--');
    setText('afterPacketLoss', '--');
    return;
  }

  setText('beforeLatency', `${preview.before.latency} ms`);
  setText('afterLatency', `${preview.after.latency} ms`);

  setText('beforeThroughput', `${preview.before.throughput} Mbps`);
  setText('afterThroughput', `${preview.after.throughput} Mbps`);

  setText('beforePacketLoss', `${Number(preview.before.packetLoss).toFixed(2)} %`);
  setText('afterPacketLoss', `${Number(preview.after.packetLoss).toFixed(2)} %`);
}

async function runScenarioSimulation() {
  const select = document.getElementById('scenarioSelect');
  if (!select) return;

  const scenario = select.value;
  console.log('Scenario đang chọn:', scenario);

  try {
    const response = await apiRequest('/api/scenario', 'POST', { scenario });
    console.log('Response scenario:', response);
    renderScenarioResult(response.scenarioResult);
  } catch (error) {
    console.error(error);
    alert(error.message || 'Scenario simulation failed');
  }
}
function renderList(items = []) {
  const recommendationList = document.getElementById('recommendationList');
  if (!recommendationList) return;

  recommendationList.innerHTML = items
    .map(
      (item) => `
        <li>
          <span class="list-icon">${item.icon}</span>
          <div>
            <strong>${item.title}</strong>
            <p>${item.description}</p>
          </div>
        </li>
      `
    )
    .join('');
}

function renderHistoryTable(data) {
  const tbody = document.getElementById('historyBody');
  if (!tbody) return;

  const rows = data.series.labels.map((label, index) => ({
    label,
    actualLatency: data.series.actualLatency[index],
    predictedLatency: data.series.predictedLatency[index],
    throughput: data.series.throughputSeries[index],
    packetLoss: data.series.packetLossSeries[index]
  }));

  tbody.innerHTML = rows
    .slice()
    .reverse()
    .slice(0, 6)
    .map(
      (row) => `
        <tr>
          <td>${row.label}</td>
          <td>${row.actualLatency} ms</td>
          <td>${row.predictedLatency} ms</td>
          <td>${row.throughput} Mbps</td>
          <td>${row.packetLoss}%</td>
        </tr>
      `
    )
    .join('');
}

function getRiskChipText(predicted, actual) {
  if (predicted - actual >= 25) return 'Critical';
  if (predicted - actual >= 12) return 'Watch';
  return 'Stable';
}

function renderDashboard(data) {
  state.data = data;

  const { metadata, computed, series, recommendations } = data;

  renderScenarioResult({
    estimatedLatency: computed.latestPredicted,
    estimatedRisk: metadata.riskLevel,
    suggestedAction: 'Review AI recommendation'
  });

  setText('locationValue', metadata.location);
  setText('uptimeValue', metadata.uptimeValue);
  setText('slaValue', metadata.slaValue);

  setText('latencyNow', computed.latestActual);
  setText('predictionNow', computed.latestPredicted);
  setText('throughputNow', computed.latestThroughput);
  setText('packetLossNow', Number(computed.latestPacketLoss).toFixed(1));

  setText('impactValue', computed.impactValue);

  setText('latencyScore', `${computed.latencyScore}%`);
  setText('throughputScore', `${computed.throughputScore}%`);
  setText('reliabilityScore', `${computed.reliabilityScore}%`);
  setText('aiScore', `${computed.aiScore}%`);

  setBar('latencyBar', computed.latencyScore);
  setBar('throughputBar', computed.throughputScore);
  setBar('reliabilityBar', computed.reliabilityScore);
  setBar('aiBar', computed.aiScore);

  setText('riskLevel', metadata.riskLevel);
  setText('slaRiskNow', metadata.riskLevel);
  setText('alertText', data.alertText);

  setText('metricChipPrediction', getRiskChipText(computed.latestPredicted, computed.latestActual));
  setText('metricChipLatency', computed.latestActual <= 60 ? 'Stable' : computed.latestActual <= 85 ? 'Watch' : 'High');
  setText('metricChipThroughput', computed.latestThroughput >= 110 ? 'Healthy' : computed.latestThroughput >= 90 ? 'Watch' : 'Low');
  setText('metricChipPacketLoss', computed.latestPacketLoss <= 0.3 ? 'Low' : computed.latestPacketLoss <= 1 ? 'Rising' : 'High');

  setText('metricChipRisk', metadata.riskLevel);
  setText('confidenceNow', `${computed.aiScore}`);
  setText('metricChipConfidence', computed.aiScore >= 90 ? 'Strong' : computed.aiScore >= 80 ? 'Estimated' : 'Review');

  setText('lastUpdatedValue', new Date(metadata.lastUpdated).toLocaleString('en-GB'));

  renderList(recommendations);
  renderHistoryTable(data);
  renderOptimizationPreview(data.optimizationPreview);
  renderChart(series);
}
function renderChart(series) {
  const ctx = document.getElementById('chart');
  if (!ctx) return;

  const config = {
    type: 'line',
    data: {
      labels: series.labels,
      datasets: [
        {
          label: 'Actual Latency (ms)',
          data: series.actualLatency,
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.14)',
          fill: true,
          tension: 0.42,
          borderWidth: 3,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: '#8fe7ff'
        },
        {
          label: 'Predicted Latency (ms)',
          data: series.predictedLatency,
          borderColor: '#9b7bff',
          backgroundColor: 'rgba(155, 123, 255, 0.08)',
          fill: false,
          tension: 0.42,
          borderWidth: 3,
          borderDash: [8, 7],
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: '#cabdff'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(7, 17, 31, 0.96)',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12,
          displayColors: true,
          titleColor: '#eff6ff',
          bodyColor: '#d8e7ff'
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: '#95a3be' }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: '#95a3be' }
        }
      }
    }
  };

  if (chart) {
    chart.data = config.data;
    chart.options = config.options;
    chart.update();
    return;
  }

  chart = new Chart(ctx, config);
}

async function apiRequest(url, method = 'GET', body) {
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });

  const rawText = await response.text();
  let data = {};

  try {
    data = rawText ? JSON.parse(rawText) : {};
  } catch (error) {
    throw new Error(`Invalid server response: ${rawText || 'Empty response body'}`);
  }

  if (!response.ok) {
    throw new Error(data.error || `Request failed with status ${response.status}`);
  }

  return data;
}

async function loadDashboard() {
  const data = await apiRequest('/api/dashboard-data');
  renderDashboard(data);
}

function updateTime() {
  const now = new Date();
  setText(
    'time',
    now.toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  );
}

function bindEvents() {
  document.getElementById('runScenarioButton')?.addEventListener('click', runScenarioSimulation);

  document.getElementById('optimizeButton')?.addEventListener('click', async () => {
  try {
    const data = await apiRequest('/api/optimize', 'POST');
    renderDashboard(data);
    setText('formStatus', 'Optimization preview generated successfully.');
  } catch (error) {
    setText('formStatus', error.message || 'Failed to optimize.');
  }
});

document.getElementById('inspectButton')?.addEventListener('click', async () => {
  try {
    const data = await apiRequest('/api/inspect', 'POST');
    renderDashboard(data);
    setText('formStatus', 'Inspection insights loaded successfully.');
  } catch (error) {
    setText('formStatus', error.message || 'Failed to inspect.');
  }
});

document.getElementById('simulateButton')?.addEventListener('click', async () => {
  try {
    const data = await apiRequest('/api/metrics/simulate', 'POST');
    renderDashboard(data);
    setText('formStatus', 'Simulated sample added successfully.');
  } catch (error) {
    setText('formStatus', error.message || 'Failed to simulate metrics.');
  }
});


document.getElementById('predictAwsButton')?.addEventListener('click', async () => {
  const button = document.getElementById('predictAwsButton');

  try {
    if (button) {
      button.disabled = true;
      button.textContent = 'Predicting from AWS...';
    }

    setText('formStatus', 'Fetching CloudWatch metrics and running AI prediction...');

    const response = await apiRequest('/api/aws/predict-from-cloudwatch', 'POST');

    // Endpoint /api/aws/predict-from-cloudwatch trả về dạng:
    // { ok, source, awsMetrics, prediction, dashboard }
    // Còn renderDashboard cần object dashboard bên trong.
    const dashboardData = response.dashboard || response;

    renderDashboard(dashboardData);

    const predictedLatency =
      response.prediction?.predicted_latency ??
      dashboardData.computed?.latestPredicted ??
      '--';

    const predictedStatus =
      response.prediction?.predicted_status ??
      dashboardData.metadata?.riskLevel ??
      '--';

    setText(
      'formStatus',
      `AWS CloudWatch prediction completed. Predicted latency: ${predictedLatency} ms, status: ${predictedStatus}.`
    );
  } catch (error) {
    console.error(error);
    setText('formStatus', error.message || 'Failed to predict from AWS CloudWatch.');
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = 'Predict from AWS CloudWatch';
    }
  }
});

document.getElementById('resetButton')?.addEventListener('click', async () => {
  try {
    const data = await apiRequest('/api/reset', 'POST');
    renderDashboard(data);
    document.getElementById('manualMetricForm')?.reset();
    setText('formStatus', 'Dashboard reset successfully.');
  } catch (error) {
    setText('formStatus', error.message || 'Failed to reset dashboard.');
  }
});
document.getElementById('manualMetricForm')?.addEventListener('submit', async (event) => {
  event.preventDefault();

  const form = event.currentTarget;
  if (!form) return;

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  try {
    const data = await apiRequest('/api/metrics/predict', 'POST', payload);
    renderDashboard(data);
    form.reset();
    setText(
      'formStatus',
      `AI prediction completed successfully. Predicted latency: ${data.computed.latestPredicted} ms, risk level: ${data.metadata.riskLevel}.`
    );
  } catch (error) {
    setText('formStatus', error.message || 'Failed to run AI prediction.');
  }
});
}
updateTime();
setInterval(updateTime, 1000);
bindEvents();
loadDashboard().catch((error) => {
  setText('formStatus', error.message || 'Failed to load dashboard.');
});
