import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the YouTube RAG Chatbot"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # ChromaDB Configuration
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    COLLECTION_NAME = "youtube_transcripts"
    
    # Text Processing Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
    
    # Retrieval Configuration
    TOP_K_RESULTS = 4
    
    # Data Storage
    TRANSCRIPTS_DIR = "./data/transcripts"
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Create necessary directories
        os.makedirs(Config.TRANSCRIPTS_DIR, exist_ok=True)
        os.makedirs(Config.CHROMA_DB_PATH, exist_ok=True)
        
        return True

# Validate configuration on import
Config.validate()