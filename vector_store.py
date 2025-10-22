import chromadb
from chromadb.config import Settings
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from config import Config

class VectorStore:
    """Manage ChromaDB operations for storing and retrieving embeddings"""
    
    def __init__(self):
        """Initialize ChromaDB client and embeddings"""
        self.embedding_function = OpenAIEmbeddings(
            openai_api_key=Config.OPENAI_API_KEY,
            model=Config.EMBEDDING_MODEL
        )
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=Config.CHROMA_DB_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=Config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"✓ ChromaDB initialized at: {Config.CHROMA_DB_PATH}")
        print(f"  Collection: {Config.COLLECTION_NAME}")
        print(f"  Current documents: {self.collection.count()}")
    
    def add_documents(self, documents: List[dict], video_id: str) -> int:
        """
        Add documents to vector store
        
        Args:
            documents: List of document dictionaries with 'text' field
            video_id: YouTube video ID for metadata
            
        Returns:
            Number of documents added
        """
        if not documents:
            raise ValueError("No documents to add")
        
        texts = [doc['text'] for doc in documents]
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_function.embed_documents(texts)
        
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
    
    def similarity_search(self, query: str, k: int = None) -> List[dict]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents with metadata and scores
        """
        k = k or Config.TOP_K_RESULTS
        
        # Generate query embedding
        query_embedding = self.embedding_function.embed_query(query)
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
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
                    'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def get_collection_stats(self) -> dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        
        stats = {
            'total_documents': count,
            'collection_name': Config.COLLECTION_NAME,
            'db_path': Config.CHROMA_DB_PATH
        }
        
        if count > 0:
            # Get sample to check video sources
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
            video_id: YouTube video ID
            
        Returns:
            Number of documents deleted
        """
        # Get all IDs for this video
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
        """Delete all documents from collection"""
        self.client.delete_collection(name=Config.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=Config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print("✓ Collection reset successfully")