import os
import chromadb
import shutil
from chromadb.config import Settings
from typing import List, Dict, Any
from config import Config
from llm_wrapper import LLMWrapper

class VectorStore:
    """Manage ChromaDB operations for storing and retrieving embeddings"""
    
    def __init__(self):
        """Initialize ChromaDB client and embeddings"""
        self.llm_wrapper = LLMWrapper()
        
        # Clean up existing DB if dimensions mismatch
        try:
            self._initialize_db()
        except Exception as e:
            if "dimension" in str(e).lower():
                print("⚠️ Embedding dimension mismatch detected. Resetting database...")
                self.cleanup_db()
                self._initialize_db()
            else:
                raise e
    
    def _initialize_db(self):
        """Initialize ChromaDB with correct settings"""
        self.client = chromadb.PersistentClient(
            path=Config.CHROMA_DB_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection with explicit dimension
        self.collection = self.client.get_or_create_collection(
            name=Config.COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine",
                "dimension": 384  # Explicitly set dimension for all-MiniLM-L6-v2
            }
        )
        
        print(f"✓ ChromaDB initialized at: {Config.CHROMA_DB_PATH}")
        print(f"  Collection: {Config.COLLECTION_NAME}")
        print(f"  Current documents: {self.collection.count()}")
    
    def cleanup_db(self):
        """Remove existing ChromaDB files"""
        if os.path.exists(Config.CHROMA_DB_PATH):
            shutil.rmtree(Config.CHROMA_DB_PATH)
            print(f"✓ Removed existing database at {Config.CHROMA_DB_PATH}")
    
    def add_documents(self, documents: List[Dict[str, Any]], video_id: str) -> int:
        """
        Add documents to vector store
        
        Args:
            documents: List of document dictionaries with 'text' and optional metadata
            video_id: YouTube video ID for document grouping
            
        Returns:
            Number of documents added
        """
        if not documents:
            raise ValueError("No documents to add")
        
        texts = [doc['text'] for doc in documents]
        
        # Generate embeddings using sentence transformers
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.llm_wrapper.get_embeddings(texts)
        
        # Prepare metadata
        metadatas = []
        ids = []
        
        for i, doc in enumerate(documents):
            doc_id = f"{video_id}_chunk_{i}"
            metadata = {
                'video_id': video_id,
                'chunk_id': doc.get('chunk_id', i),
                'chunk_size': doc.get('chunk_size', len(doc['text'])),
                'source': doc.get('url', f"https://www.youtube.com/watch?v={video_id}")
            }
            
            ids.append(doc_id)
            metadatas.append(metadata)
        
        # Add to ChromaDB
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✓ Added {len(documents)} documents to ChromaDB")
        print(f"  Total documents in collection: {self.collection.count()}")
        
        return len(documents)
    
    def similarity_search(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query string
            k: Number of results to return (default: Config.TOP_K_RESULTS)
            
        Returns:
            List of dictionaries containing matched documents and metadata
        """
        k = k or Config.TOP_K_RESULTS
        
        # Generate query embedding
        query_embedding = self.llm_wrapper.get_embeddings(query)
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                result = {
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity': 1 - results['distances'][0][i]
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection
        
        Returns:
            Dictionary containing collection statistics
        """
        count = self.collection.count()
        
        stats = {
            'total_documents': count,
            'collection_name': Config.COLLECTION_NAME,
            'db_path': str(Config.CHROMA_DB_PATH)
        }
        
        if count > 0:
            sample = self.collection.get(limit=min(count, 100))
            video_ids = set()
            
            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    if 'video_id' in metadata:
                        video_ids.add(metadata['video_id'])
            
            stats['unique_videos'] = len(video_ids)
            stats['video_ids'] = list(video_ids)
        
        return stats
    
    def delete_video(self, video_id: str) -> int:
        """
        Delete all chunks for a specific video
        
        Args:
            video_id: YouTube video ID to delete
            
        Returns:
            Number of documents deleted
        """
        results = self.collection.get(
            where={"video_id": video_id}
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
            count = len(results['ids'])
            print(f"✓ Deleted {count} documents for video: {video_id}")
            return count
        
        print(f"No documents found for video: {video_id}")
        return 0
    
    def reset_collection(self):
        """Delete all documents from collection and recreate it"""
        self.client.delete_collection(name=Config.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=Config.COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine",
                "dimension": 384  # Explicitly set dimension for all-MiniLM-L6-v2
            }
        )
        print("✓ Collection reset successfully")