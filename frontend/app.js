/**
 * Enterprise Knowledge Navigator - Frontend Controller
 * Connects to live FastAPI backend endpoints and renders real system telemetry.
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

  const infoAppName = document.getElementById('infoAppName');
  const infoEnv = document.getElementById('infoEnv');
  const infoPython = document.getElementById('infoPython');
  const infoDb = document.getElementById('infoDb');
  const storageList = document.getElementById('storageList');

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
      
      engineStatus.textContent = 'Connected (FastAPI)';
      dbStatus.textContent = data.database_connected ? 'Connected (SQLite)' : 'Disconnected';
      storageStatus.textContent = data.storage_directories_ready ? 'Verified & Ready' : 'Incomplete';
      versionStatus.textContent = `v${data.version} (${data.environment})`;

      sidebarStatusDot.classList.add('online');
      sidebarStatusText.textContent = 'System Online';

      return data;
    } catch (err) {
      healthBadge.textContent = 'OFFLINE';
      healthBadge.className = 'status-pill status-loading';
      engineStatus.textContent = 'Connection Error';
      dbStatus.textContent = 'Unavailable';
      storageStatus.textContent = 'Unavailable';
      versionStatus.textContent = 'Offline';

      sidebarStatusDot.classList.remove('online');
      sidebarStatusText.textContent = 'System Offline';
      console.error('Failed to probe backend health:', err);
      return null;
    }
  }

  async function fetchSystemInfo() {
    try {
      const res = await fetch('/api/v1/system/info');
      if (res.ok) {
        const data = await res.json();
        if (infoAppName) infoAppName.textContent = data.project_name;
        if (infoEnv) infoEnv.textContent = data.environment;
        if (infoPython) infoPython.textContent = `Python ${data.python_version}`;
        if (infoDb) infoDb.textContent = data.database_url;

        if (storageList && data.storage_status) {
          storageList.innerHTML = `
            <li><span>Raw Documents Directory:</span> <strong class="badge-status ${data.storage_status.raw_docs_dir ? 'status-ok' : 'status-fail'}">${data.storage_status.raw_docs_dir ? 'Verified' : 'Missing'}</strong></li>
            <li><span>Processed Documents Directory:</span> <strong class="badge-status ${data.storage_status.processed_docs_dir ? 'status-ok' : 'status-fail'}">${data.storage_status.processed_docs_dir ? 'Verified' : 'Missing'}</strong></li>
            <li><span>Vector Store Directory:</span> <strong class="badge-status ${data.storage_status.vector_store_dir ? 'status-ok' : 'status-fail'}">${data.storage_status.vector_store_dir ? 'Verified' : 'Missing'}</strong></li>
            <li><span>Graph Store Directory:</span> <strong class="badge-status ${data.storage_status.graph_store_dir ? 'status-ok' : 'status-fail'}">${data.storage_status.graph_store_dir ? 'Verified' : 'Missing'}</strong></li>
            <li><span>Operational Logs Directory:</span> <strong class="badge-status ${data.storage_status.logs_dir ? 'status-ok' : 'status-fail'}">${data.storage_status.logs_dir ? 'Verified' : 'Missing'}</strong></li>
          `;
        }
      }
    } catch (e) {
      console.error('Failed to fetch system info:', e);
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
    fetchSystemInfo();
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

  // ML Engine Lab Controls
  const runSimilarityBtn = document.getElementById('runSimilarityBtn');
  const runClusterBtn = document.getElementById('runClusterBtn');
  const mlQueryInput = document.getElementById('mlQueryInput');
  const mlOutputStatus = document.getElementById('mlOutputStatus');
  const mlJsonDisplay = document.getElementById('mlJsonDisplay');
  const copyMlJsonBtn = document.getElementById('copyMlJsonBtn');

  let lastMlData = null;

  const sampleCorpus = [
    "Employees are permitted to work remotely up to two days per week with manager approval under the flexible work policy.",
    "The corporate health insurance policy covers annual medical examinations, dental, and hospitalization benefits.",
    "Quarterly financial earnings report indicates enterprise revenue growth of twelve percent across international markets.",
    "Server infrastructure deployment requires containerization with Docker and orchestration via Kubernetes clusters."
  ];

  if (runSimilarityBtn) {
    runSimilarityBtn.addEventListener('click', async () => {
      const query = mlQueryInput.value.trim() || "remote work policy";
      mlOutputStatus.textContent = "Computing Scikit-Learn TF-IDF Cosine Similarity...";
      mlJsonDisplay.textContent = "// Calculating vector space angles...";

      try {
        const startTime = performance.now();
        const res = await fetch('/api/v1/ml/similarity', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query, documents: sampleCorpus })
        });
        const duration = (performance.now() - startTime).toFixed(1);
        const data = await res.json();
        lastMlData = data;
        mlOutputStatus.textContent = `Scikit-Learn TF-IDF: Completed in ${duration} ms (HTTP ${res.status})`;
        mlJsonDisplay.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        mlOutputStatus.textContent = "Error computing similarity";
        mlJsonDisplay.textContent = `// Error: ${err.message}`;
      }
    });
  }

  if (runClusterBtn) {
    runClusterBtn.addEventListener('click', async () => {
      mlOutputStatus.textContent = "Executing Scikit-Learn K-Means (K=2) Clustering...";
      mlJsonDisplay.textContent = "// Fitting centroids and extracting dominant terms...";

      try {
        const startTime = performance.now();
        const res = await fetch('/api/v1/ml/cluster', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ documents: sampleCorpus, num_clusters: 2 })
        });
        const duration = (performance.now() - startTime).toFixed(1);
        const data = await res.json();
        lastMlData = data;
        mlOutputStatus.textContent = `Scikit-Learn K-Means: Completed in ${duration} ms (HTTP ${res.status})`;
        mlJsonDisplay.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        mlOutputStatus.textContent = "Error executing clustering";
        mlJsonDisplay.textContent = `// Error: ${err.message}`;
      }
    });
  }

  if (copyMlJsonBtn) {
    copyMlJsonBtn.addEventListener('click', () => {
      if (lastMlData) {
        navigator.clipboard.writeText(JSON.stringify(lastMlData, null, 2));
        const orig = copyMlJsonBtn.textContent;
        copyMlJsonBtn.textContent = 'Copied!';
        setTimeout(() => { copyMlJsonBtn.textContent = orig; }, 1500);
      }
    });
  }

  // Initial execution
  fetchHealth();
  fetchSystemInfo();
  testEndpoint('/api/v1/health');
});
