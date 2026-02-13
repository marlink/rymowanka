import './style.css'

const API_URL = 'http://localhost:8000';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1500;

const generateBtn = document.getElementById('generate-btn');
const verseInput = document.getElementById('verse-input');
const resultsArea = document.getElementById('results');
const loadingIndicator = document.getElementById('loading-indicator');

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
    if (type !== 'error') setTimeout(() => { statusBanner.style.display = 'none'; }, 3000);
}
function hideStatus() { statusBanner.style.display = 'none'; }

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
            } else throw err;
        }
    }
}

async function checkBackend() {
    try { await fetch(`${API_URL}/docs`, { method: 'HEAD', mode: 'no-cors' }); }
    catch { showStatus('⚠ Backend offline — start server.py on :8000', 'error'); }
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

        if (data.mode === 'word') {
            renderWordMode(data);
        } else {
            renderVerseMode(data);
        }
        showStatus('✓ Generated — hit again for new suggestions', 'success');
    } catch (error) {
        console.error(error);
        showStatus('Backend offline — start server.py on :8000', 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Magic';
        loadingIndicator.style.display = 'none';
    }
}

// --- WORD MODE: show rhyming words in PERFECT / DOMINANT / NEAR columns ---
function renderWordMode(data) {
    const cols = ['PERFECT', 'DOMINANT', 'NEAR'];
    resultsArea.innerHTML = '';

    cols.forEach(grade => {
        const col = document.createElement('div');
        col.className = `mode-column ${grade.toLowerCase()}`;

        const h3 = document.createElement('h3');
        h3.textContent = grade;
        col.appendChild(h3);

        const list = document.createElement('div');
        const items = data.words?.[grade] || [];

        if (items.length === 0) {
            list.innerHTML = '<div class="empty-state">No matches</div>';
        } else {
            items.forEach(item => {
                const card = document.createElement('div');
                card.className = 'stanza-card';
                card.innerHTML = `
                    <div class="stanza-content">
                        <div class="stanza-line verse-line"><span class="rhyme-highlight">${item.word}</span></div>
                    </div>
                    <div class="stanza-meta">
                        <span class="badge badge-${grade.toLowerCase()}">${grade}</span>
                        <span class="score">${Math.round(item.score * 100)}%</span>
                    </div>
                `;
                card.addEventListener('click', () => copyCard(card, item.word, item.score));
                list.appendChild(card);
            });
        }

        col.appendChild(list);
        resultsArea.appendChild(col);
    });

    resultsArea.classList.add('visible');
}

// --- VERSE MODE: show one verse per AABB / ABAB / ABBA column ---
function renderVerseMode(data) {
    const schemes = ['AABB', 'ABAB', 'ABBA'];
    resultsArea.innerHTML = '';

    schemes.forEach(scheme => {
        const col = document.createElement('div');
        col.className = 'mode-column';

        const h3 = document.createElement('h3');
        h3.textContent = scheme;
        col.appendChild(h3);

        const item = data.verses?.[scheme];

        if (!item) {
            col.innerHTML += '<div class="empty-state">No matching verse found</div>';
        } else {
            seenLines.push(item.line);

            const lineWords = item.line.split(' ');
            const lastWord = lineWords.pop();
            const lineStart = lineWords.join(' ');

            const card = document.createElement('div');
            card.className = 'stanza-card';
            card.innerHTML = `
                <div class="stanza-content">
                    <div class="stanza-line verse-line">${lineStart} <span class="rhyme-highlight">${lastWord}</span></div>
                </div>
                <div class="stanza-meta">
                    <span class="badge badge-perfect">${scheme}</span>
                    <span class="score">${Math.round(item.score * 100)}%</span>
                </div>
            `;
            card.addEventListener('click', () => copyCard(card, item.line, item.score));
            col.appendChild(card);
        }

        resultsArea.appendChild(col);
    });

    resultsArea.classList.add('visible');
}

function copyCard(card, text, score) {
    navigator.clipboard.writeText(text).then(() => {
        card.classList.add('copied');
        const s = card.querySelector('.score');
        if (s) s.textContent = '✓ Copied!';
        setTimeout(() => {
            card.classList.remove('copied');
            if (s) s.textContent = `${Math.round(score * 100)}%`;
        }, 800);
    });
}

// Reset seen when last word changes
let lastWord = '';
verseInput.addEventListener('input', () => {
    const curr = verseInput.value.trim().split(/\s+/).pop()?.toLowerCase() || '';
    if (curr !== lastWord) { seenLines = []; lastWord = curr; }
});

generateBtn.addEventListener('click', generate);
verseInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') generate();
});
checkBackend();
