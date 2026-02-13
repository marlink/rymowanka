from polish_rhyme_util import count_syllables, get_phonetic_suffix, RhymeFinder
from context_agent import ContextAgent

class PolishPoet:
    def __init__(self, mode="AABB"):
        self.mode = mode
        self.finder = RhymeFinder()
        self.context_agent = ContextAgent()
        
    def analyze_context_logic(self, lines):
        # Using the ContextAgent to perform semantic analysis on the whole verse
        return self.context_agent.analyze_semantic_flow(lines)

    def filter_vocabulary(self, word):
        # Filter out archaic words (staropolskie)
        # Allow common swear words (wulgaryzmy) for authenticity in modern speech
        # This list would be expanded in a production environment
        archaic_terms = ["azaliż", "bialogłowa", "kajet", "onuca", "przasnysz"]
        if word.lower() in archaic_terms:
            return False
        return True

    def find_rhymes_for_line(self, line):
        words = line.split()
        if not words: return []
        last_word = words[-1]
        
        # 1. Phonetic Suffix
        suffix = get_phonetic_suffix(last_word)
        
        # 2. Find rhymes
        raw_rhymes = self.finder.find_rhymes(last_word, limit=50)
        
        # 3. Filter rhymes
        valid_rhymes = []
        for r in raw_rhymes:
            # Filter archaic
            if not self.filter_vocabulary(r):
                continue
            # Logic check (stub) - e.g. don't rhyme "chleb" with "niebo" if context is sad? 
            # For now, just pass.
            valid_rhymes.append(r)
            
        return valid_rhymes[:10]

    def generate_report(self, lines):
        print(f"\n--- POETIC REPORT [Mode: {self.mode}] ---")
        print(f"{'Line Content':<40} | {'Syllables':<10} | {'Suffix'}")
        print("-" * 65)
        
        # 1. Logic Check (Whole verse analysis via Agent)
        passed, report = self.analyze_context_logic(lines)
        if not passed:
             print(f"⚠️ AGENT WARNING: {report}")
        else:
             print(f"✅ AGENT LOGIC PASS: {report}")

        previous_line = None
        for line in lines:
            words = line.split()
            if not words: continue
            last_word = words[-1]
            
            # 2. Filter Check
            if not all(self.filter_vocabulary(w) for w in words):
                 print(f"⚠️ WARNING: Archaic word detected in line: {line}")
            
            s_count = sum(count_syllables(w) for w in words)
            suffix = get_phonetic_suffix(last_word)
            print(f"{line:<40} | {s_count:<10} | {suffix}")
            previous_line = line
            
    def suggest_real_rhymes(self, word):
        print(f"\nReal rhymes for '{word}' from dictionary:")
        rhymes = self.finder.find_rhymes(word)
        if rhymes:
            print(", ".join(rhymes))
        else:
            print("No real rhymes found in dictionary.")

# Configuration
modes = {
    "AABB": ["Ciemny las szumi pieśń o poranku", "Złoty blask tańczy na szklanym dzbanku", "Wiatr delikatnie gałęzie kołysze", "Wszyscy dokoła kochają te cisze"],
    "ABAB": ["Gdy noc zapada nad wielkim miastem", "Gwiazdy mrugają do nas z wysoka", "Czas płynie wolno pod srebrnym piastem", "Zasypia powoli ziemia głęboka"],
    "ABBA": ["Słońce zachodzi krwawo nad polem", "Ptaki już dawno do gniazd powróciły", "Ostatnie iskry dnia się wypaliły", "Cisza zamieszkała pod wspólnym stołem"]
}

poet = PolishPoet()
for mode, content in modes.items():
    poet.mode = mode
    poet.generate_report(content)

# Test Real Word Rhymes
test_words = ["miasto", "woda", "miłość", "serce"]
for word in test_words:
    poet.suggest_real_rhymes(word)
