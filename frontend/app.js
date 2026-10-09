const modelSelect = document.getElementById('model-select');
const systemPrompt = document.getElementById('system-prompt');
const promptBox = document.getElementById('prompt-box');
const responseBox = document.getElementById('response-box');
const statusPill = document.getElementById('status-pill');
const submitBtn = document.getElementById('submit-btn');
const clearBtn = document.getElementById('clear-btn');

async function fetchModels() {
  try {
    const res = await fetch('/api/models');
    const data = await res.json();

    if (!Array.isArray(data.models) || data.models.length === 0) {
      throw new Error('No models found');
    }

    modelSelect.innerHTML = '';
    data.models.forEach((model) => {
      const option = document.createElement('option');
      option.value = model;
      option.textContent = model;
      modelSelect.appendChild(option);
    });

    if (data.default_model) {
      modelSelect.value = data.default_model;
    }

    statusPill.textContent = 'Local service ready';
    statusPill.style.background = 'rgba(72, 191, 227, 0.14)';
  } catch (error) {
    statusPill.textContent = 'Ollama not ready';
    statusPill.style.background = 'rgba(255, 153, 0, 0.14)';
    responseBox.textContent = 'The local model service is not responding. Start Ollama and pull a model, for example: docker exec -it llm-ollama ollama pull llama3.2';
  }
}

async function submitPrompt() {
  const prompt = promptBox.value.trim();
  if (!prompt) {
    responseBox.textContent = 'Please enter a prompt.';
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Running...';
  responseBox.textContent = 'Generating response...';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: modelSelect.value,
        prompt,
        system: systemPrompt.value.trim() || 'You are a helpful assistant.'
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Request failed');
    }

    responseBox.textContent = data.response || 'No output returned.';
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
