#!/usr/bin/env python3
"""
Script to generate PNG image of the incident analysis LangGraph workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph import incident_graph

def generate_graph_image():
    """Generate PNG image of the LangGraph workflow"""
    try:
        # Generate PNG bytes
        png_bytes = incident_graph.get_graph().draw_mermaid_png()

        # Save to file
        output_path = os.path.join(os.path.dirname(__file__), "incident-analysis-workflow.png")
        with open(output_path, "wb") as f:
            f.write(png_bytes)

        print(f"Graph image saved to: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error generating graph image: {e}")
        return None

if __name__ == "__main__":
    generate_graph_image()