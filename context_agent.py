import re

class ContextAgent:
    """
    Sub-agent responsible for narrative flow and logical consistency of Polish verses.
    In a production environment, this would interface with an LLM (Gemini/GPT).
    Currently, it implements heuristic-based checks and a 'Review' interface for an AI assistant.
    """
    
    def __init__(self, tone="modern_rap"):
        self.tone = tone

    def analyze_semantic_flow(self, lines):
        """
        Analyzes if lines have a logical connection using thematic clustering and connectors.
        """
        if len(lines) < 2:
            return True, "Solitary line, flow is neutral."

        # Thematic clusters for Polish Rap (Heuristic mapping)
        clusters = [
            {'natura', 'pole', 'ogień', 'wiatr', 'las', 'słońce', 'ptaki', 'cisza'},
            {'miasto', 'beton', 'bloki', 'ulica', 'raper', 'trampki', 'pliki'},
            {'technologia', 'kod', 'sieć', 'ai', 'ekran', 'cyfrowy', 'dane'},
            {'emocje', 'serce', 'miłość', 'ból', 'trud', 'marzenie', 'dusza'}
        ]

        flow_score = 0
        feedback = []

        # 1. Broad Topic Check (Thematic Consistency)
        verse_words = set(re.findall(r'\w+', " ".join(lines).lower()))
        matched_clusters = [c for c in clusters if len(c.intersection(verse_words)) >= 2]
        
        if matched_clusters:
            flow_score += 1 # Topical consistency found
        
        # 2. Sequential Logic 
        for i in range(len(lines) - 1):
            l1, l2 = lines[i].lower(), lines[i+1].lower()
            w1 = set(re.findall(r'\w+', l1))
            w2 = set(re.findall(r'\w+', l2))
            
            # Connectors
            if any(m in l2 for m in ['bo ', 'więc ', 'ale ', 'lecz ', 'i ', 'a ']):
                flow_score += 0.5
                
            # Direct word repetition (cohesion)
            if w1.intersection(w2):
                flow_score += 0.5

        is_logical = flow_score >= 1.0
        status = "LOGICAL" if is_logical else "POTENTIALLY DISJOINTED"
        
        return is_logical, f"Status: {status} (Score: {flow_score})"

    def simulate_llm_critique(self, verse):
        """
        Simulates an LLM agent reviewing the verse for real-world 'vibe' and logic.
        """
        # This method is designed to be called by the main engine to provide
        # 'Agent-level' feedback on generated content.
        logic_pass, flow_info = self.analyze_semantic_flow(verse)
        
        return {
            "passed": logic_pass,
            "agent_report": flow_info,
            "suggestions": "Ensure the subject of the first line is addressed or contrasted in the second." if not logic_pass else "Flow is consistent."
        }

if __name__ == "__main__":
    # Test with a disjointed verse
    test_verse = [
        "Jem dzisiaj pyszne drugie śniadanie",
        "Betonowe bloki stoją o ścianie"
    ]
    agent = ContextAgent()
    passed, report = agent.analyze_semantic_flow(test_verse)
    print(f"Flow Check: {passed} | {report}")
