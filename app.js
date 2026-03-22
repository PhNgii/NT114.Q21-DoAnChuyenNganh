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
  setText('alertText', data.alertText);
  setText('metricChipPrediction', getRiskChipText(computed.latestPredicted, computed.latestActual));
  setText('metricChipLatency', computed.latestActual <= 60 ? 'Stable' : 'Degraded');
  setText('metricChipThroughput', computed.latestThroughput >= 110 ? 'Healthy' : 'Warning');
  setText('metricChipPacketLoss', computed.latestPacketLoss <= 0.3 ? 'Low' : 'Rising');
  setText('lastUpdatedValue', new Date(metadata.lastUpdated).toLocaleString('en-GB'));

  renderList(recommendations);
  renderHistoryTable(data);
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

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
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
  document.getElementById('optimizeButton')?.addEventListener('click', async () => {
    const data = await apiRequest('/api/optimize', 'POST');
    renderDashboard(data);
  });

  document.getElementById('inspectButton')?.addEventListener('click', async () => {
    const data = await apiRequest('/api/inspect', 'POST');
    renderDashboard(data);
  });

  document.getElementById('simulateButton')?.addEventListener('click', async () => {
    const data = await apiRequest('/api/metrics/simulate', 'POST');
    renderDashboard(data);
  });

  document.getElementById('resetButton')?.addEventListener('click', async () => {
    const data = await apiRequest('/api/reset', 'POST');
    renderDashboard(data);
    document.getElementById('manualMetricForm')?.reset();
  });

  document.getElementById('manualMetricForm')?.addEventListener('submit', async (event) => {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const payload = Object.fromEntries(formData.entries());

    try {
      const data = await apiRequest('/api/metrics/manual', 'POST', payload);
      renderDashboard(data);
      event.currentTarget.reset();
      setText('formStatus', 'Đã thêm mẫu dữ liệu mới thành công.');
    } catch (error) {
      setText('formStatus', error.message);
    }
  });
}

updateTime();
setInterval(updateTime, 1000);
bindEvents();
loadDashboard().catch((error) => {
  setText('formStatus', error.message);
});
