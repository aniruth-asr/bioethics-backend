import sys
import json
import logging
from engine.pipeline import run_full_pipeline, warmup_model
from engine.knowledge_base import REGULATORY_CLAUSES, KNOWLEDGE_BASE

# Silence noisy external logs
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

def print_separator():
    print("=" * 80)

def main():
    print_separator()
    print("BIOETHICS RADAR - SEMANTIC GRADING DEBUGGER")
    print("This script runs the core pipeline locally and shows exactly how an input")
    print("is scored against the official regulatory clauses.")
    print_separator()

    # Pre-warm the semantic model
    print("Loading AI model and regulatory embeddings... (this may take a few seconds)")
    warmup_model()

    print("\n[READY] Enter or paste the text of the paper you want to grade.")
    print("When you are finished, press Enter on an empty line, then press Ctrl+Z (Windows) or Ctrl+D (Mac/Linux), then Enter.")
    
    # Read input from user
    input_lines = sys.stdin.readlines()
    test_text = "".join(input_lines).strip()

    if not test_text:
        print("\nNo text provided. Exiting.")
        return

    print("\n" + "-" * 80)
    print(f"Analyzing {len(test_text)} characters...")
    print("-" * 80 + "\n")

    # Run the exact same pipeline the FastAPI server uses
    results = run_full_pipeline(test_text)

    # Print a detailed report
    for pillar_id, data in results.items():
        pillar_name = data['pillar']['name']
        score = data['score']
        evidence = data['evidence']
        findings = data['findings']

        print(f"PILLAR: {pillar_name.upper()}")
        print(f"SCORE:  {score} / 100")
        
        # Show exactly which official guidelines are being evaluated
        print("\n  Graded Against Official Clauses:")
        for clause in REGULATORY_CLAUSES.get(pillar_id, []):
            print(f"    - [{clause['source']}] {clause['text'][:120]}...")

        print("\n  Semantic Engine Evidence Found in Input:")
        if not evidence:
            print("    [!] No strong compliance semantic matches found.")
        else:
            for ev in evidence:
                similarity_pct = ev['similarity'] * 100
                print(f"    - ({similarity_pct:.1f}% Match) \"{ev['span'][:150]}...\"")

        print("\n  Key Findings:")
        for f in findings:
            symbol = "✅" if f['type'] == 'ok' else "⚠️" if f['type'] == 'warn' else "❌"
            print(f"    {symbol} {f['text']}")

        print_separator()

if __name__ == "__main__":
    main()
