const modelList = document.getElementById('model-list');
const systemPrompt = document.getElementById('system-prompt');
const promptBox = document.getElementById('prompt-box');
const responseBox = document.getElementById('response-box');
const statusPill = document.getElementById('status-pill');
const submitBtn = document.getElementById('submit-btn');
const clearBtn = document.getElementById('clear-btn');

let availableModels = [];

function getSelectedModels() {
  const checked = [...document.querySelectorAll('#model-list input[type="checkbox"]:checked')];
  return checked.map((checkbox) => checkbox.value);
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
            stream: true
          }
        : {
            models: selectedModels,
            prompt,
            system: systemPrompt.value.trim() || 'You are a helpful assistant.',
            stream: false
          };

    if (selectedModels.length === 1) {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let text = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        text += decoder.decode(value, { stream: true });
        responseBox.textContent = text;
      }

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
  } catch (error) {
    responseBox.textContent = `Request failed: ${error.message}`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Run';
  }
}

clearBtn.addEventListener('click', () => {
  promptBox.value = '';
  responseBox.textContent = 'Awaiting input...';
});

submitBtn.addEventListener('click', submitPrompt);

fetchModels();
