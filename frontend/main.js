import './style.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
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
    statusBanner.style.background = type === 'error' ? '#D64444' : type === 'warn' ? '#BB974D' : '#84EB0C';
    statusBanner.style.color = type === 'success' ? '#0F0F12' : '#fff';
    if (type !== 'error') setTimeout(() => { statusBanner.style.display = 'none'; }, 3000);
}
function hideStatus() { statusBanner.style.display = 'none'; }

async function fetchWithRetry(url, options, retries = MAX_RETRIES) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const r = await fetch(url, options);
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            hideStatus();
            return r;
        } catch (err) {
            if (attempt < retries) {
                showStatus(`Retry ${attempt}/${retries - 1}...`, 'warn');
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
        data.mode === 'word' ? renderWordMode(data) : renderVerseMode(data);
        showStatus('✓ Hit Generate again for fresh suggestions', 'success');
    } catch (error) {
        console.error(error);
        showStatus('Backend offline — start server.py on :8000', 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate 🎤';
        loadingIndicator.style.display = 'none';
    }
}

// --- WORD MODE: 3 columns ---
function renderWordMode(data) {
    resultsArea.innerHTML = '';
    const grades = ['PERFECT', 'DOMINANT', 'NEAR'];

    grades.forEach(grade => {
        const col = document.createElement('div');
        col.className = 'mode-column';

        const h3 = document.createElement('h3');
        h3.textContent = grade;
        col.appendChild(h3);

        const items = data.words?.[grade] || [];
        if (!items.length) {
            col.innerHTML += '<div class="empty-state">—</div>';
        } else {
            items.forEach(item => {
                const card = document.createElement('div');
                const flags = item.flags || [];
                let classes = 'stanza-card';
                let icon = '';

                if (flags.includes('vulgar')) {
                    classes += ' is-vulgar';
                }
                if (flags.includes('entity')) {
                    classes += ' is-entity';
                    icon = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="#FFD700" stroke="#FFD700" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-star"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg> `;
                }

                card.className = classes;
                card.innerHTML = `
                    <div class="stanza-content">
                        <div class="stanza-line verse-line">
                           ${icon}<span class="rhyme-highlight">${item.word}</span>
                        </div>
                    </div>
                    <div class="stanza-meta">
                        <span class="badge badge-${grade.toLowerCase()}">${grade}</span>
                        <span class="score">${Math.round(item.score * 100)}%</span>
                    </div>`;
                card.addEventListener('click', () => copyCard(card, item.word, item.score));
                col.appendChild(card);
            });
        }
        resultsArea.appendChild(col);
    });
    resultsArea.classList.add('visible');
}

// --- VERSE MODE: single ranked list ---
function renderVerseMode(data) {
    resultsArea.innerHTML = '';

    const col = document.createElement('div');
    col.className = 'mode-column verse-results';

    const header = document.createElement('h3');
    const inputSyl = data.input_syllables || '?';
    header.innerHTML = `Rhyming lines <span class="rhyme-tail-badge">-${data.rhyme_tail}</span> <span class="syl-info">${inputSyl} syl</span>`;
    col.appendChild(header);

    const verses = data.verses || [];
    if (!verses.length) {
        col.innerHTML += '<div class="empty-state">No rhyming verses found in corpus. Try a different ending word.</div>';
    } else {
        verses.forEach(item => {
            seenLines.push(item.line);
            if (seenLines.length > 50) seenLines.shift();

            const words = item.line.split(' ');
            const lastWord = words.pop();
            const lineStart = words.join(' ');

            const sylMatch = data.input_syllables
                ? (item.syllables === data.input_syllables ? '✓' : `${item.syllables}`)
                : item.syllables;

            const card = document.createElement('div');
            card.className = 'stanza-card';
            card.innerHTML = `
                <div class="stanza-content">
                    <div class="stanza-line verse-line">${lineStart} <span class="rhyme-highlight">${lastWord}</span></div>
                </div>
                <div class="stanza-meta">
                    <span class="syl-badge">${sylMatch} syl</span>
                    <span class="score">${Math.round(item.score * 100)}%</span>
                </div>`;
            card.addEventListener('click', () => copyCard(card, item.line, item.score));
            col.appendChild(card);
        });
    }

    resultsArea.appendChild(col);
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
