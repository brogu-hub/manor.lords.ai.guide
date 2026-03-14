// Manor Lords AI Advisor — Dashboard Client

const statusEl = document.getElementById('status');

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
    });

    evtSource.addEventListener('state', (e) => {
        const data = JSON.parse(e.data);
        renderState(data);
    });

    evtSource.onerror = () => {
        statusEl.textContent = 'Reconnecting...';
        statusEl.className = 'status disconnected';
    };
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
}

function renderState(state) {
    // Could render raw state details if needed
}

// Follow-up questions
document.getElementById('ask-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('ask-input');
    const question = input.value.trim();
    if (!question) return;

    input.value = '';
    const resp = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
    });
    const data = await resp.json();

    // Show the answer in the situation panel temporarily
    const situationEl = document.querySelector('#situation .panel-content');
    situationEl.innerHTML = `<p><strong>Q:</strong> ${question}</p><p>${data.answer}</p>`;
});

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

// Start SSE connection
connectSSE();
