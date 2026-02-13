import re
from collections import defaultdict, namedtuple

# Precompile Regex Patterns
RE_DZI = re.compile(r'dzi')
RE_DZ_ZH = re.compile(r'dż|rz')
RE_CH = re.compile(r'ch')
RE_SOFTEN = {
    'ci': re.compile(r'ci(?=[aeąęioóuy])'),
    'si': re.compile(r'si(?=[aeąęioóuy])'),
    'zi': re.compile(r'zi(?=[aeąęioóuy])'),
    'ni': re.compile(r'ni(?=[aeąęioóuy])'),
}
RE_NASAL_END_A = re.compile(r'ą$')
RE_NASAL_END_E = re.compile(r'ę$')
RE_NASAL_SZ = re.compile(r'ą(?=[szżźćfwšč])')
RE_NASAL_EZ = re.compile(r'ę(?=[szżźćfwšč])')
RE_NON_ALPHANUM = re.compile(r'[^\w]')

WordEntry = namedtuple('WordEntry', ['original', 'normalized', 'vowels', 'tail_d2', 'tail_d1'])

class PhoneticEngine:
    def __init__(self, vocabulary=None):
        self.vowels = 'aeąęiouóuy'
        self.en_digraphs = {
            'design': 'dizajn', 'business': 'biznes', 'flow': 'floł', 'show': 'szoł',
            'online': 'onlajn', 'deadline': 'dedlajn', 'vibe': 'wajb', 'style': 'stajl'
        }
        
        self.index_d2 = defaultdict(list)
        self.index_d1 = defaultdict(list)
        self.word_map = {} # original -> WordEntry
        
        if vocabulary:
            self.build_index(vocabulary)

    def normalize(self, word):
        w = word.lower()
        w = self.en_digraphs.get(w, w)
        
        # Table-based/Regex-lite transforms
        w = RE_DZI.sub('dź', w)
        w = RE_DZ_ZH.sub('ż', w)
        w = RE_CH.sub('h', w)
        
        for char, reg in RE_SOFTEN.items():
            w = reg.sub(char[0] + 'i', w)
            
        w = w.replace('ó', 'u').replace('y', 'i')
        w = RE_NASAL_END_A.sub('om', w)
        w = RE_NASAL_END_E.sub('em', w)
        
        # Simplification for indexing
        w = w.translate(str.maketrans('łńśćźż', 'lnsczz'))
        return w

    def get_vowel_positions(self, word):
        return [i for i, c in enumerate(word) if c in self.vowels]

    def build_entry(self, word):
        norm = self.normalize(word)
        v_pos = self.get_vowel_positions(norm)
        
        tail_d1 = norm[v_pos[-1]:] if v_pos else norm
        tail_d2 = norm[v_pos[-2]:] if len(v_pos) >= 2 else tail_d1
        
        return WordEntry(word, norm, len(v_pos), tail_d2, tail_d1)

    def build_index(self, vocabulary):
        for word in vocabulary:
            entry = self.build_entry(word)
            self.word_map[word] = entry
            self.index_d2[entry.tail_d2].append(entry)
            self.index_d1[entry.tail_d1].append(entry)

    def find_candidates(self, target_word):
        target = self.build_entry(target_word)
        
        # Tier 1: Multi-syllabic exact match
        perfect = self.index_d2.get(target.tail_d2, [])
        
        # Tier 2: Single-vowel exact match (filter out those already in perfect)
        near_candidates = self.index_d1.get(target.tail_d1, [])
        
        # Filter and score 
        results = []
        seen = {target.original}
        
        for cand in perfect:
            if cand.original in seen: continue
            score = self.score(target, cand, True)
            results.append((cand.original, "PERFECT", score))
            seen.add(cand.original)
            
        for cand in near_candidates:
            if cand.original in seen: continue
            score = self.score(target, cand, False)
            grade = "DOMINANT" if score > 0.7 else "NEAR"
            results.append((cand.original, grade, score))
            seen.add(cand.original)
            
        return sorted(results, key=lambda x: x[2], reverse=True)

    def score(self, t, c, is_d2):
        score = 1.0 if is_d2 else 0.8
        # Flow penalty
        syll_diff = abs(t.vowels - c.vowels)
        if syll_diff > 1: score *= 0.6
        elif syll_diff == 1: score *= 0.9
        return score
