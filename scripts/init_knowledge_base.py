from pathlib import Path
import sys

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from rag.vector_store import VectorStoreService  # noqa: E402


def main() -> None:
    print("[init] Loading documents from data/ into Chroma...")
    VectorStoreService().load_document()
    print("[init] Knowledge base is ready.")


if __name__ == "__main__":
    main()
