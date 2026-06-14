"""Build the Chroma index from the study files in /data. Run once before serving:
    python ingest.py
"""

from app.repository import index

if __name__ == "__main__":
    count = index()
    print(f"Indexed {count} documents (study summaries + quotes) into Chroma.")
