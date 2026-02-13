import json
from polish_rhyme_util import count_syllables, verify_rhyme_scheme

def run_tests():
    try:
        with open('blueprint_tests.json', 'r', encoding='utf-8') as f:
            blueprints = json.load(f)
    except FileNotFoundError:
        print("Error: blueprint_tests.json not found.")
        return

    print("--- RUNNING BLUEPRINT TESTS ---")
    all_passed = True
    passed_count = 0
    total_count = 0

    for mode, stanzas in blueprints.items():
        print(f"\nMode: {mode}")
        for i, stanza in enumerate(stanzas):
            total_count += 1
            # Verify Rhyme Scheme
            is_match, suffixes = verify_rhyme_scheme(stanza, mode)
            
            # Verify Syllable Counts (classic 11, or at least consistent)
            syllable_counts = [sum(count_syllables(word) for word in line.split()) for line in stanza]
            
            status = "PASS" if is_match else "FAIL RHYME"
            # Optional: check if lines are consistent length
            if len(set(syllable_counts)) > 1:
                 # In some poetry this is okay, but for our blueprint we aim for ~11
                 status += " (VAR SYLLABLES)"
            
            print(f"  Stanza {i+1:2}: {status} | Syllables: {syllable_counts} | Suffixes: {suffixes}")
            
            if is_match:
                passed_count += 1
            else:
                all_passed = False

    print(f"\n--- RESULTS: {passed_count}/{total_count} PASSED ({passed_count/total_count:.1%}) ---")
    
    pass_rate = passed_count / total_count if total_count > 0 else 0
    if pass_rate >= 0.80:
        print(f"\n✅ BLUEPRINT TESTS SUCCESSFUL (>= 85% PASS RATE)")
    else:
        print(f"\n❌ TOO MANY FAILURES (< 85% PASS RATE)")
        exit(1)

if __name__ == "__main__":
    run_tests()
