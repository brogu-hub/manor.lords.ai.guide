// Manor Lords AI Advisor — Dashboard Client

const statusEl = document.getElementById('status');
const processBtn = document.getElementById('process-btn');
const saveSelect = document.getElementById('save-select');

// Load available saves into dropdown
async function loadSaves() {
    try {
        const resp = await fetch('/api/saves');
        const data = await resp.json();
        saveSelect.innerHTML = '<option value="">Latest save</option>';
        for (const s of data.saves) {
            const opt = document.createElement('option');
            opt.value = s.name;
            opt.textContent = s.name.replace('.sav', '');
            saveSelect.appendChild(opt);
        }
    } catch { /* ignore */ }
}

// SSE connection for real-time updates
function connectSSE() {
    const evtSource = new EventSource('/api/stream');

    evtSource.onopen = () => {
        statusEl.textContent = 'Connected';
        statusEl.className = 'status connected';
    };

    evtSource.addEventListener('advice', (e) => {
        const data = JSON.parse(e.data);
        renderAdvice(data);
        processBtn.disabled = false;
        processBtn.textContent = 'Analyse Save';
    });

    evtSource.addEventListener('state', (e) => {
        const data = JSON.parse(e.data);
        renderState(data);
    });

    evtSource.addEventListener('processing', (e) => {
        statusEl.textContent = 'Analysing save...';
        statusEl.className = 'status processing';
        processBtn.disabled = true;
        processBtn.textContent = 'Analysing...';
    });

    evtSource.addEventListener('error', (e) => {
        try {
            const data = JSON.parse(e.data);
            statusEl.textContent = 'Error: ' + (data.message || 'Pipeline failed');
        } catch {
            statusEl.textContent = 'Pipeline error';
        }
        statusEl.className = 'status disconnected';
        processBtn.disabled = false;
        processBtn.textContent = 'Analyse Save';
    });

    evtSource.onerror = () => {
        statusEl.textContent = 'Reconnecting...';
        statusEl.className = 'status disconnected';
    };
}

async function processLatest() {
    processBtn.disabled = true;
    processBtn.textContent = 'Analysing...';
    statusEl.textContent = 'Processing save file...';
    statusEl.className = 'status processing';

    try {
        const selected = saveSelect.value;
        const url = selected ? `/api/process?save_name=${encodeURIComponent(selected)}` : '/api/process';
        const resp = await fetch(url, { method: 'POST' });
        const data = await resp.json();
        if (data.status === 'error' || data.status === 'busy') {
            statusEl.textContent = data.message;
            statusEl.className = 'status disconnected';
            processBtn.disabled = false;
            processBtn.textContent = 'Analyse Save';
        }
        // On success, keep button disabled — SSE 'advice' event will re-enable it
    } catch (err) {
        statusEl.textContent = 'Error: ' + err.message;
        statusEl.className = 'status disconnected';
        processBtn.disabled = false;
        processBtn.textContent = 'Analyse Save';
    }
}

function renderAdvice(advice) {
    // Warnings
    const warningsEl = document.querySelector('#warnings .panel-content');
    if (advice.warnings && advice.warnings.length > 0) {
        warningsEl.innerHTML = advice.warnings
            .map(w => `<div class="warning-item">${w}</div>`)
            .join('');
    } else {
        warningsEl.innerHTML = '<p class="placeholder">No warnings — settlement stable</p>';
    }

    // Priorities
    const prioritiesEl = document.querySelector('#priorities .panel-content');
    const priorities = [advice.priority_1, advice.priority_2, advice.priority_3].filter(Boolean);
    if (priorities.length > 0) {
        prioritiesEl.innerHTML = priorities
            .map((p, i) => `<div class="priority-item"><strong>#${i + 1}</strong> ${p}</div>`)
            .join('');
    }

    // Situation
    const situationEl = document.querySelector('#situation .panel-content');
    if (advice.situation) {
        situationEl.innerHTML = `<p>${advice.situation}</p>`;
    }

    // Next Season
    const nextSeasonEl = document.querySelector('#next-season .panel-content');
    if (advice.next_season) {
        nextSeasonEl.innerHTML = `<p>${advice.next_season}</p>`;
    }

    statusEl.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    statusEl.className = 'status connected';
}

function renderState(state) {
    const bar = document.getElementById('state-bar');
    bar.classList.remove('hidden');

    const meta = state.meta || {};
    const res = state.resources || {};
    const settle = state.settlement || {};
    const pop = settle.population || {};
    const food = res.food || {};
    const alerts = state.alerts || [];

    document.getElementById('s-year').textContent = meta.year || '-';
    document.getElementById('s-season').textContent = meta.season || '-';
    document.getElementById('s-families').textContent = pop.families || '-';

    const foodVal = document.getElementById('s-food');
    const foodTotal = typeof food.total === 'number' ? Math.round(food.total) : '-';
    foodVal.textContent = foodTotal;
    foodVal.className = 'state-value' + (foodTotal !== '-' && foodTotal < 20 ? ' critical' : '');

    const approvalVal = document.getElementById('s-approval');
    const approvalNum = typeof settle.approval === 'number' ? Math.round(settle.approval) : '-';
    approvalVal.textContent = approvalNum !== '-' ? approvalNum + '%' : '-';
    approvalVal.className = 'state-value' + (approvalNum !== '-' && approvalNum < 50 ? ' critical' : '');

    const alertsEl = document.getElementById('s-alerts');
    alertsEl.textContent = alerts.length;
    alertsEl.className = 'state-value' + (alerts.length > 0 ? ' critical' : '');
}

// Follow-up questions
const chatMessages = document.getElementById('chat-messages');

document.getElementById('ask-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('ask-input');
    const question = input.value.trim();
    if (!question) return;

    // Show user question
    chatMessages.innerHTML += `<div class="chat-msg user"><strong>You:</strong> ${escapeHtml(question)}</div>`;
    input.value = '';

    // Show loading
    const loadingEl = document.createElement('div');
    loadingEl.className = 'chat-msg ai loading';
    loadingEl.textContent = 'Thinking...';
    chatMessages.appendChild(loadingEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const resp = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
    });
    const data = await resp.json();

    // Replace loading with answer
    loadingEl.className = 'chat-msg ai';
    loadingEl.innerHTML = `<strong>Advisor:</strong> ${data.answer}`;
    chatMessages.scrollTop = chatMessages.scrollHeight;
});

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Session history rendering
function renderHistory(entries) {
    const historyEl = document.querySelector('#history .panel-content');
    if (!entries || entries.length === 0) {
        historyEl.innerHTML = '<p class="placeholder">No saves analysed yet</p>';
        return;
    }
    historyEl.innerHTML = entries
        .map(e => `<div class="priority-item"><strong>${e.timestamp}</strong> ${e.summary}</div>`)
        .join('');
}

// Start
connectSSE();
loadSaves();
