"""Basic usage example for DeepProbe."""

import sys
import os

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from deep_probe import DeepProbe

# Initialize the client (uses GEMINI_API_KEY environment variable)
probe = DeepProbe()

# Run deep research
result = probe.research("What are the main applications of quantum computing?")

# Print the report
print("=" * 60)
print("RESEARCH REPORT")
print("=" * 60)
print(result.report)
print()

# Print metadata
print(f"Interaction ID: {result.interaction_id}")
print(f"Status: {result.status.value}")
print(f"Tokens used: {result.cost_usage.total_tokens}")

# Print sources
if result.sources:
    print("\nSources:")
    for i, source in enumerate(result.sources, 1):
        print(f"  {i}. {source.title or source.url}")

# Save to file
result.save("quantum_computing_report.md")
print("\nReport saved to quantum_computing_report.md")