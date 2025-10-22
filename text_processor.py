from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Updated import
from config import Config

class TextProcessor:
    """Process and chunk text for embedding"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize text processor
        
        Args:
            chunk_size: Size of each text chunk
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size or Config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def split_text(self, text: str, metadata: dict = None) -> List[dict]:
        """
        Split text into chunks with metadata
        
        Args:
            text: Text to split
            metadata: Additional metadata to attach to each chunk
            
        Returns:
            List of dictionaries containing text chunks and metadata
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                'text': chunk,
                'chunk_id': i,
                'chunk_size': len(chunk)
            }
            
            # Add custom metadata
            if metadata:
                doc.update(metadata)
            
            documents.append(doc)
        
        print(f"✓ Split text into {len(documents)} chunks")
        print(f"  Chunk size: {self.chunk_size}, Overlap: {self.chunk_overlap}")
        
        return documents
    
    def get_chunk_stats(self, documents: List[dict]) -> dict:
        """Get statistics about chunks"""
        if not documents:
            return {}
        
        chunk_sizes = [doc['chunk_size'] for doc in documents]
        
        return {
            'total_chunks': len(documents),
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'total_characters': sum(chunk_sizes)
        }