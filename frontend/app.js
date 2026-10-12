const modelList = document.getElementById('model-list');
const provenanceList = document.getElementById('provenance-list');
const systemPrompt = document.getElementById('system-prompt');
const promptBox = document.getElementById('prompt-box');
const responseBox = document.getElementById('response-box');
const statusPill = document.getElementById('status-pill');
const localStatus = document.getElementById('local-status');
const uncensoredStatus = document.getElementById('uncensored-status');
const uncensoredToggle = document.getElementById('uncensored-toggle');
const uncensoredNote = document.getElementById('uncensored-note');
const submitBtn = document.getElementById('submit-btn');
const clearBtn = document.getElementById('clear-btn');
const historyList = document.getElementById('history-list');

let availableModels = [];
let uncensoredModeEnabled = false;

function updateUncensoredUI() {
  uncensoredToggle.checked = uncensoredModeEnabled;
  uncensoredStatus.textContent = uncensoredModeEnabled ? 'Uncensored mode: on' : 'Uncensored mode: off';
  uncensoredStatus.classList.toggle('warning-pill', !uncensoredModeEnabled);
  uncensoredStatus.classList.toggle('success-pill', uncensoredModeEnabled);
  uncensoredNote.classList.toggle('hidden', !uncensoredModeEnabled);
}

function getSelectedModels() {
  const checked = [...document.querySelectorAll('#model-list input[type="checkbox"]:checked')];
  return checked.map((checkbox) => checkbox.value);
}

async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();

    localStatus.textContent = data.local_only ? 'Local-only: on' : 'Local-only: off';
    localStatus.classList.toggle('info-pill', data.local_only);
    localStatus.classList.toggle('warning-pill', !data.local_only);

    uncensoredModeEnabled = Boolean(data.uncensored_mode);
    updateUncensoredUI();
  } catch (error) {
    localStatus.textContent = 'Local-only: unknown';
    uncensoredStatus.textContent = 'Uncensored mode: unknown';
  }
}

async function fetchHistory() {
  try {
    const res = await fetch('/api/history?limit=5');
    const data = await res.json();
    const items = Array.isArray(data.history) ? data.history : [];

    if (!items.length) {
      historyList.innerHTML = '<li class="history-empty">No local activity yet.</li>';
      return;
    }

    historyList.innerHTML = items
      .map((item) => {
        const payload = item.payload || {};
        const summary = payload.prompt || payload.models || 'Local activity';
        const title = payload.model || (Array.isArray(payload.models) ? payload.models.join(', ') : item.kind);
        return `
          <li class="history-item">
            <div class="history-title">${title}</div>
            <div class="history-summary">${String(summary).slice(0, 120)}</div>
            <div class="history-meta">${item.kind} • ${item.timestamp ? new Date(item.timestamp).toLocaleString() : 'local'}</div>
          </li>
        `;
      })
      .join('');
  } catch (error) {
    historyList.innerHTML = '<li class="history-empty">History unavailable.</li>';
  }
}

async function fetchProvenance() {
  try {
    const res = await fetch('/api/models/provenance');
    const data = await res.json();
    const models = Array.isArray(data.models) ? data.models : [];

    if (!models.length) {
      provenanceList.innerHTML = '<li class="history-empty">No provenance metadata available.</li>';
      return;
    }

    provenanceList.innerHTML = models
      .map((item) => {
        const checksum = item.checksum ? item.checksum.slice(0, 12) : 'n/a';
        const size = item.size ? `${(item.size / 1024 / 1024).toFixed(1)} MiB` : 'unknown';
        return `
          <li class="provenance-item">
            <div class="history-title">${item.name}</div>
            <div class="history-summary">${item.source} • ${size}</div>
            <div class="history-meta">checksum: ${checksum}</div>
          </li>
        `;
      })
      .join('');
  } catch (error) {
    provenanceList.innerHTML = '<li class="history-empty">Provenance unavailable.</li>';
  }
}

async function fetchModels() {
  try {
    const res = await fetch('/api/models');
    const data = await res.json();

    if (!Array.isArray(data.models) || data.models.length === 0) {
      throw new Error('No models found');
    }

    availableModels = data.models;
    modelList.innerHTML = '';

    availableModels.forEach((model) => {
      const option = document.createElement('label');
      option.className = 'model-option';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.value = model;
      checkbox.checked = model === data.default_model;

      const labelText = document.createElement('span');
      labelText.textContent = model;

      option.appendChild(checkbox);
      option.appendChild(labelText);
      modelList.appendChild(option);
    });

    statusPill.textContent = 'Local service ready';
    statusPill.style.background = 'rgba(72, 191, 227, 0.14)';
    fetchProvenance();
  } catch (error) {
    statusPill.textContent = 'Ollama not ready';
    statusPill.style.background = 'rgba(255, 153, 0, 0.14)';
    responseBox.textContent = 'The local model service is not responding. Start Ollama and pull a model, for example: docker exec -it llm-ollama ollama pull llama3.2';
  }
}

function renderCompareResults(results) {
  if (!Array.isArray(results) || results.length === 0) {
    responseBox.textContent = 'No results returned.';
    return;
  }

  const cards = results
    .map(
      (result) => `
        <article class="model-card">
          <div class="model-card-header">${result.model}</div>
          <div class="model-card-body">${(result.response || 'No response.').replace(/\n/g, '<br>')}</div>
        </article>
      `
    )
    .join('');

  responseBox.innerHTML = `<div class="compare-grid">${cards}</div>`;
}

async function submitPrompt() {
  const prompt = promptBox.value.trim();
  if (!prompt) {
    responseBox.textContent = 'Please enter a prompt.';
    return;
  }

  const selectedModels = getSelectedModels();
  if (selectedModels.length === 0) {
    responseBox.textContent = 'Please select at least one model.';
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Running...';
  responseBox.textContent = 'Generating response...';

  try {
    const endpoint = selectedModels.length === 1 ? '/api/chat' : '/api/compare';
    const body =
      selectedModels.length === 1
        ? {
            model: selectedModels[0],
            prompt,
            system: systemPrompt.value.trim() || 'You are a helpful assistant.',
            stream: true,
            uncensored: uncensoredModeEnabled
          }
        : {
            models: selectedModels,
            prompt,
            system: systemPrompt.value.trim() || 'You are a helpful assistant.',
            stream: false,
            uncensored: uncensoredModeEnabled
          };

    if (selectedModels.length === 1) {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Request failed');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let text = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        text += decoder.decode(value, { stream: true });
        responseBox.textContent = text;
      }

      fetchHistory();
      return;
    }

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Request failed');
    }

    renderCompareResults(data.results || []);
    fetchHistory();
  } catch (error) {
    responseBox.textContent = `Request failed: ${error.message}`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Run';
  }
}

uncensoredToggle.addEventListener('change', () => {
  const next = uncensoredToggle.checked;
  if (next) {
    const confirmed = window.confirm(
      'Enabling uncensored mode can expose unfiltered model outputs. Continue only if you understand the risks and local legal requirements.'
    );
    if (!confirmed) {
      uncensoredToggle.checked = false;
      uncensoredModeEnabled = false;
      updateUncensoredUI();
      return;
    }
  }

  uncensoredModeEnabled = next;
  updateUncensoredUI();
});

clearBtn.addEventListener('click', () => {
  promptBox.value = '';
  responseBox.textContent = 'Awaiting input...';
});

submitBtn.addEventListener('click', submitPrompt);

fetchStatus();
fetchModels();
fetchHistory();
