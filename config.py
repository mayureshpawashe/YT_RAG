import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the YouTube RAG Chatbot"""

    # === Groq settings ===
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    # === Model settings ===
    LLM_MODEL = "openai/gpt-oss-120b"  # Groq model
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # === LLM parameters ===
    TEMPERATURE = 0.7
    MAX_TOKENS = 8192
    REASONING_EFFORT = "medium"

    # === ChromaDB Configuration ===
    BASE_DB_DIR = os.path.join(os.getcwd(), "chroma_db_runs")
    RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
    CHROMA_DB_PATH = os.path.join(BASE_DB_DIR, f"run_{RUN_ID}")
    COLLECTION_NAME = "youtube_transcripts"

    # === Text Processing ===
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

    # === Retrieval ===
    TOP_K_RESULTS = 4

    # === Data Storage ===
    TRANSCRIPTS_DIR = "./data/transcripts"

    # === Cleanup Configuration ===
    CLEANUP_ENABLED = os.getenv("CLEANUP_ENABLED", "true").lower() == "true"
    CLEANUP_RETENTION_DAYS = int(os.getenv("CLEANUP_RETENTION_DAYS", 7))
    CLEANUP_RETENTION_COUNT = int(os.getenv("CLEANUP_RETENTION_COUNT", 3))
    CLEANUP_RETENTION_MODE = os.getenv("CLEANUP_RETENTION_MODE", "hybrid")  # "days", "count", "hybrid"

    @staticmethod
    def validate():
        """Validate required config and create necessary directories"""
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        os.makedirs(Config.TRANSCRIPTS_DIR, exist_ok=True)
        os.makedirs(Config.CHROMA_DB_PATH, exist_ok=True)
        print(f"[Config] ✅ Chroma path initialized at: {Config.CHROMA_DB_PATH}")
        return True


# Validate on import
Config.validate()
