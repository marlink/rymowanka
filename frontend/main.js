import './style.css'

const API_URL = 'http://localhost:8000';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1500;

const generateBtn = document.getElementById('generate-btn');
const verseInput = document.getElementById('verse-input');
const resultsArea = document.getElementById('results');
const loadingIndicator = document.getElementById('loading-indicator');

const lists = {
    PERFECT: document.getElementById('perfect-list'),
    DOMINANT: document.getElementById('dominant-list'),
    NEAR: document.getElementById('near-list')
};

// --- Status banner ---
const statusBanner = document.createElement('div');
statusBanner.id = 'status-banner';
statusBanner.style.cssText = 'display:none;padding:10px 20px;text-align:center;font-size:13px;font-weight:600;position:fixed;top:0;left:0;right:0;z-index:999;transition:all 0.3s ease;';
document.body.prepend(statusBanner);

function showStatus(msg, type = 'error') {
    statusBanner.textContent = msg;
    statusBanner.style.display = 'block';
    statusBanner.style.background = type === 'error' ? '#ff4444' : type === 'warn' ? '#ff8800' : '#22cc66';
    statusBanner.style.color = '#fff';
    if (type !== 'error') {
        setTimeout(() => { statusBanner.style.display = 'none'; }, 3000);
    }
}

function hideStatus() {
    statusBanner.style.display = 'none';
}

// --- Fetch with retry ---
async function fetchWithRetry(url, options, retries = MAX_RETRIES) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            hideStatus();
            return response;
        } catch (err) {
            if (attempt < retries) {
                showStatus(`Backend unreachable — retry ${attempt}/${retries - 1}...`, 'warn');
                await new Promise(r => setTimeout(r, RETRY_DELAY * attempt));
            } else {
                throw err;
            }
        }
    }
}

// --- Health check on load ---
async function checkBackend() {
    try {
        await fetch(`${API_URL}/docs`, { method: 'HEAD', mode: 'no-cors' });
    } catch {
        showStatus('⚠ Backend offline — start server.py on :8000', 'error');
    }
}

async function generate() {
    const verse = verseInput.value.trim();
    if (!verse) return;

    generateBtn.disabled = true;
    loadingIndicator.style.display = 'block';
    resultsArea.classList.remove('visible');

    try {
        const response = await fetchWithRetry(`${API_URL}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ verse })
        });

        const data = await response.json();
        renderResults(data.suggestions);
        showStatus('✓ Generated', 'success');
    } catch (error) {
        console.error(error);
        showStatus('Backend offline — start server.py on :8000, then try again', 'error');
    } finally {
        generateBtn.disabled = false;
        loadingIndicator.style.display = 'none';
    }
}

function renderResults(suggestions) {
    Object.keys(lists).forEach(key => {
        if (lists[key]) lists[key].innerHTML = '';
    });

    Object.keys(suggestions).forEach(grade => {
        const container = lists[grade];
        if (!container) return;

        const items = suggestions[grade];
        if (items.length === 0) {
            container.innerHTML = '<div class="empty-state">No matches found</div>';
            return;
        }

        items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'stanza-card';

            card.innerHTML = `
                <div class="stanza-content">
                    <div class="stanza-line rhyme-line">${item.word}</div>
                </div>
                <div class="stanza-meta">
                    <span class="badge">${item.grade}</span>
                    <span class="score">${Math.round(item.score * 100)}% Match</span>
                </div>
            `;

            card.addEventListener('click', () => {
                navigator.clipboard.writeText(item.word).then(() => {
                    card.classList.add('copied');
                    setTimeout(() => card.classList.remove('copied'), 400);
                });
            });

            container.appendChild(card);
        });
    });

    resultsArea.classList.add('visible');
}

generateBtn.addEventListener('click', generate);

verseInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        generate();
    }
});

// Check backend on page load
checkBackend();
