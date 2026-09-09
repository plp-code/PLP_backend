import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from src.python.app.core.database import Base  

import src.python.app.models 

try:
    from eralchemy2 import render_er
except ImportError:
    print("Error: eralchemy2 is required. Run: pip install eralchemy2 pygraphviz")
    sys.exit(1)


def generate_erd(output_file: str = "erd.png"):
    """
    Generates an ERD from SQLAlchemy metadata.
    Supported extensions: .png, .pdf, .svg, .dot, .md (Mermaid)
    """
    print(f"Generating ERD for {len(Base.metadata.tables)} tables...")

    render_er(Base.metadata, output_file)
    print(f"ERD successfully saved to: {output_file}")


if __name__ == "__main__":
    generate_erd("erd.png")