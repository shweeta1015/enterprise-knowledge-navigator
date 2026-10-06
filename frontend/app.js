/**
 * Enterprise Knowledge Navigator - Frontend Controller (Sprint 1)
 * Connects to live FastAPI backend endpoints and renders health metrics.
 */

document.addEventListener('DOMContentLoaded', () => {
  const refreshBtn = document.getElementById('refreshStatusBtn');
  const healthBadge = document.getElementById('healthBadge');
  const engineStatus = document.getElementById('engineStatus');
  const dbStatus = document.getElementById('dbStatus');
  const storageStatus = document.getElementById('storageStatus');
  const versionStatus = document.getElementById('versionStatus');
  const sidebarStatusDot = document.getElementById('sidebarStatusDot');
  const sidebarStatusText = document.getElementById('sidebarStatusText');
  const jsonDisplay = document.getElementById('jsonDisplay');
  const outputStatus = document.getElementById('outputStatus');
  const copyBtn = document.getElementById('copyJsonBtn');
  const endpointBtns = document.querySelectorAll('.endpoint-btn');

  let lastResponseData = null;

  async function fetchHealth() {
    healthBadge.textContent = 'Checking...';
    healthBadge.className = 'status-pill status-loading';
    sidebarStatusText.textContent = 'Checking...';

    try {
      const response = await fetch('/api/v1/health');
      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }
      const data = await response.json();
      
      // Update UI with real server data
      healthBadge.textContent = data.status.toUpperCase();
      healthBadge.className = data.status === 'healthy' ? 'status-pill status-healthy' : 'status-pill status-loading';
      
      engineStatus.textContent = 'Online (FastAPI)';
      dbStatus.textContent = data.database_connected ? 'Connected (SQLite)' : 'Disconnected';
      storageStatus.textContent = data.storage_directories_ready ? 'Initialized (6/6)' : 'Incomplete';
      versionStatus.textContent = `v${data.version} (${data.environment})`;

      sidebarStatusDot.classList.add('online');
      sidebarStatusText.textContent = 'System Operational';

      return data;
    } catch (err) {
      healthBadge.textContent = 'OFFLINE';
      healthBadge.className = 'status-pill status-loading';
      engineStatus.textContent = 'Connection Error';
      dbStatus.textContent = 'Unavailable';
      storageStatus.textContent = 'Unavailable';
      versionStatus.textContent = 'Offline';

      sidebarStatusDot.classList.remove('online');
      sidebarStatusText.textContent = 'Backend Offline';
      console.error('Failed to probe backend health:', err);
      return null;
    }
  }

  async function testEndpoint(url) {
    outputStatus.textContent = `Querying ${url}...`;
    jsonDisplay.textContent = '// Fetching data...';

    try {
      const startTime = performance.now();
      const res = await fetch(url);
      const duration = (performance.now() - startTime).toFixed(1);
      const data = await res.json();
      
      lastResponseData = data;
      outputStatus.textContent = `Status: ${res.status} ${res.statusText} (${duration} ms)`;
      jsonDisplay.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      outputStatus.textContent = `Status: Error connecting`;
      jsonDisplay.textContent = `// Error fetching ${url}:\n${err.message}`;
    }
  }

  // Event Listeners
  refreshBtn.addEventListener('click', () => {
    fetchHealth();
    testEndpoint('/api/v1/health');
  });

  endpointBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      endpointBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const url = btn.getAttribute('data-url');
      testEndpoint(url);
    });
  });

  copyBtn.addEventListener('click', () => {
    if (lastResponseData) {
      navigator.clipboard.writeText(JSON.stringify(lastResponseData, null, 2));
      const originalText = copyBtn.textContent;
      copyBtn.textContent = 'Copied!';
      setTimeout(() => {
        copyBtn.textContent = originalText;
      }, 1500);
    }
  });

  // Initial execution
  fetchHealth();
  testEndpoint('/api/v1/health');
});
