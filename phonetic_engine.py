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
        self.index_vowels = defaultdict(list) # New: Assonance index
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
        """
        Get vowel positions, skipping 'i' when it acts as a consonant softener.
        """
        positions = []
        for i, c in enumerate(word):
            if c not in self.vowels:
                continue
            # Skip softening 'i': preceded by consonant AND followed by vowel
            if c == 'i' and i > 0 and word[i - 1] not in self.vowels:
                if i + 1 < len(word) and word[i + 1] in self.vowels:
                    continue
            positions.append(i)
        return positions

    def build_entry(self, word):
        norm = self.normalize(word)
        v_pos = self.get_vowel_positions(norm)
        
        tail_d1 = norm[v_pos[-1]:] if v_pos else norm
        tail_d2 = norm[v_pos[-2]:] if len(v_pos) >= 2 else tail_d1
        
        # Extract vowels string for assonance (e.g., 'kawa' -> 'aa')
        vowel_seq = "".join([norm[i] for i in v_pos])
        # We only really care about the last 2-3 vowels for rhyming
        if len(vowel_seq) > 2:
            vowel_seq = vowel_seq[-2:]
        
        return WordEntry(word, norm, len(v_pos), tail_d2, tail_d1), vowel_seq

    def build_index(self, vocabulary):
        for word in vocabulary:
            entry, vowel_seq = self.build_entry(word)
            self.word_map[word] = entry
            self.index_d2[entry.tail_d2].append(entry)
            self.index_d1[entry.tail_d1].append(entry)
            # Only index assonance if we have at least 1 vowel
            if vowel_seq:
                self.index_vowels[vowel_seq].append(entry)

    def find_candidates(self, target_word):
        entry_tuple = self.build_entry(target_word)
        target = entry_tuple[0]
        target_vowels = entry_tuple[1]
        
        # Tier 1: Multi-syllabic exact match (real rhymes)
        perfect = self.index_d2.get(target.tail_d2, [])
        
        # Filter and score 
        results = []
        seen = {target.original}
        
        for cand in perfect:
            if cand.original in seen: continue
            score = self.score(target, cand, 'PERFECT')
            results.append((cand.original, "PERFECT", score))
            seen.add(cand.original)

        # Tier 2: Single-vowel match (Weak Rhymes)
        if len(target.tail_d1) >= 3:
            near_candidates = self.index_d1.get(target.tail_d1, [])
            for cand in near_candidates:
                if cand.original in seen: continue
                # Limit checking to prevent timeouts on common sounds
                # (simple heuristic constraint)
                if len(seen) > 2000: break 
                
                score = self.score(target, cand, 'NEAR')
                grade = "NEAR"
                results.append((cand.original, grade, score))
                seen.add(cand.original)
        
        # Tier 3: Assonance (Vowel Match) - The "Rap Rhyme"
        # This captures "kawa" ~ "mapa" (aa ~ aa)
        if target_vowels:
            assonance_candidates = self.index_vowels.get(target_vowels, [])
            # IMPORTANT: Assonance lists can be huge (all words ending in 'a' or 'e')
            # So we must sample or traverse carefully. 
            # We shuffle or just take the first N? The vocab is sorted alphabetically usually.
            # Ideally we'd prefer words with same syllable count.
            
            count = 0
            for cand in assonance_candidates:
                if cand.original in seen: continue
                
                # Soft limit for performance
                if count > 3000: break
                count += 1

                # Heuristic: Match syllable count for better flow
                is_same_len = (cand.vowels == target.vowels)
                
                score = 0.6 # Base score for assonance
                if is_same_len: score += 0.1
                
                # If consonant skeleton matches partially?
                # For now just classify as DOMINANT if same syll + matched vowels
                grade = "DOMINANT" if is_same_len else "NEAR"
                
                results.append((cand.original, grade, score))
                seen.add(cand.original)
            
        return sorted(results, key=lambda x: x[2], reverse=True)

    def score(self, t, c, mode):
        # Base scores
        if mode == 'PERFECT': score = 1.0
        elif mode == 'NEAR': score = 0.7
        else: score = 0.5
        
        # Penalty for syllable count mismatch
        syll_diff = abs(t.vowels - c.vowels)
        if syll_diff > 1: score *= 0.8
        elif syll_diff == 1: score *= 0.95
        
        return score
