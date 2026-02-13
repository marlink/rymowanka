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

// Track seen lines to avoid repeats
let seenLines = [];

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
    generateBtn.textContent = '⟳ Generating...';
    loadingIndicator.style.display = 'block';
    resultsArea.classList.remove('visible');

    try {
        const response = await fetchWithRetry(`${API_URL}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ verse, seen: seenLines })
        });

        const data = await response.json();
        renderResults(data);
        showStatus('✓ Generated', 'success');
    } catch (error) {
        console.error(error);
        showStatus('Backend offline — start server.py on :8000, then try again', 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Magic';
        loadingIndicator.style.display = 'none';
    }
}

function renderResults(data) {
    const { suggestions, original_word, original_verse } = data;

    Object.keys(lists).forEach(key => {
        if (lists[key]) lists[key].innerHTML = '';
    });

    let hasResults = false;

    Object.keys(suggestions).forEach(grade => {
        const container = lists[grade];
        if (!container) return;

        const items = suggestions[grade];
        if (items.length === 0) {
            container.innerHTML = '<div class="empty-state">No verse matches</div>';
            return;
        }

        hasResults = true;

        items.forEach(item => {
            // Track this line so it won't repeat
            seenLines.push(item.line);

            const card = document.createElement('div');
            card.className = 'stanza-card';

            // Highlight the rhyming word at the end
            const lineWords = item.line.split(' ');
            const lastWord = lineWords.pop();
            const lineStart = lineWords.join(' ');

            card.innerHTML = `
                <div class="stanza-content">
                    <div class="stanza-line verse-line">${lineStart} <span class="rhyme-highlight">${lastWord}</span></div>
                </div>
                <div class="stanza-meta">
                    <span class="badge badge-${grade.toLowerCase()}">${grade}</span>
                    <span class="score">${Math.round(item.score * 100)}%</span>
                </div>
            `;

            card.addEventListener('click', () => {
                navigator.clipboard.writeText(item.line).then(() => {
                    card.classList.add('copied');
                    const orig = card.querySelector('.stanza-meta .score');
                    if (orig) { orig.textContent = '✓ Copied!'; }
                    setTimeout(() => {
                        card.classList.remove('copied');
                        if (orig) { orig.textContent = `${Math.round(item.score * 100)}%`; }
                    }, 800);
                });
            });

            container.appendChild(card);
        });
    });

    if (!hasResults) {
        lists.PERFECT.innerHTML = '<div class="empty-state">No matching verses found in corpus. Try a different line.</div>';
    }

    resultsArea.classList.add('visible');
}

// Reset seen lines when input changes significantly
let lastVerse = '';
verseInput.addEventListener('input', () => {
    const current = verseInput.value.trim();
    // If the last word changed, reset seen
    const currLast = current.split(/\s+/).pop()?.toLowerCase() || '';
    const prevLast = lastVerse.split(/\s+/).pop()?.toLowerCase() || '';
    if (currLast !== prevLast) {
        seenLines = [];
    }
    lastVerse = current;
});

generateBtn.addEventListener('click', generate);

verseInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        generate();
    }
});

checkBackend();
