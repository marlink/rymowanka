import './style.css'

const generateBtn = document.getElementById('generate-btn');
const verseInput = document.getElementById('verse-input');
const resultsArea = document.getElementById('results');
const loadingIndicator = document.getElementById('loading-indicator');

const lists = {
    PERFECT: document.getElementById('perfect-list'),
    DOMINANT: document.getElementById('dominant-list'),
    NEAR: document.getElementById('near-list')
};

async function generate() {
    const verse = verseInput.value.trim();
    if (!verse) return;

    generateBtn.disabled = true;
    loadingIndicator.style.display = 'block';
    resultsArea.classList.remove('visible');

    try {
        const response = await fetch('http://localhost:8000/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ verse })
        });

        if (!response.ok) throw new Error('API Error');

        const data = await response.json();
        renderResults(data.suggestions);
    } catch (error) {
        console.error(error);
        alert('Failed to generate rhymes. Ensure backend is running at :8000');
    } finally {
        generateBtn.disabled = false;
        loadingIndicator.style.display = 'none';
    }
}

function renderResults(suggestions) {
    // Clear lists
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
