import os
import time
import shutil
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from config import Config
from llm_wrapper import LLMWrapper


class VectorStore:
    """Manage ChromaDB operations for storing and retrieving embeddings"""

    def __init__(self):
        self.llm_wrapper = LLMWrapper()

        # Each run uses a unique folder (defined in config)
        self.ensure_db_path_exists()
        self._initialize_db()

    def ensure_db_path_exists(self):
        """Ensure DB folder exists with writable permissions"""
        os.makedirs(Config.CHROMA_DB_PATH, exist_ok=True)

        # Fix permissions if necessary
        try:
            os.chmod(Config.CHROMA_DB_PATH, 0o777)
        except Exception as e:
            print(f"⚠️ Could not chmod folder: {e}")

        time.sleep(0.3)  # give filesystem time to settle

        if not os.access(Config.CHROMA_DB_PATH, os.W_OK):
            raise PermissionError(f"🚫 Path not writable: {Config.CHROMA_DB_PATH}")

        print(f"📁 Chroma DB directory ready: {Config.CHROMA_DB_PATH}")

    def _initialize_db(self):
        """Initialize ChromaDB client"""
        print(f"🚀 Initializing Chroma at: {Config.CHROMA_DB_PATH}")

        self.client = chromadb.PersistentClient(
            path=Config.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )

        self.collection = self.client.get_or_create_collection(
            name=Config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "dimension": 384}
        )

        print(f"✅ Fresh ChromaDB ready at: {Config.CHROMA_DB_PATH}")
        print(f"   Collection: {Config.COLLECTION_NAME}")
        print(f"   Docs: {self.collection.count()}")

    def add_documents(self, documents: List[Dict[str, Any]], video_id: str) -> int:
        """Add documents (chunks) to Chroma collection"""
        if not documents:
            raise ValueError("No documents to add")

        texts = [doc["text"] for doc in documents]
        print(f"🧠 Generating embeddings for {len(texts)} chunks...")
        embeddings = self.llm_wrapper.get_embeddings(texts)

        ids, metadatas = [], []
        for i, doc in enumerate(documents):
            ids.append(f"{video_id}_chunk_{i}")
            metadatas.append({
                "video_id": video_id,
                "chunk_id": i,
                "chunk_size": len(doc["text"]),
                "source": f"https://www.youtube.com/watch?v={video_id}"
            })

        try:
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            raise

        print(f"✅ Added {len(documents)} docs. Total: {self.collection.count()}")
        return len(documents)

    def similarity_search(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """Search for relevant chunks"""
        k = k or Config.TOP_K_RESULTS
        query_embedding = self.llm_wrapper.get_embeddings(query)
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            include=['documents', 'metadatas', 'distances']
        )

        formatted = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity': 1 - results['distances'][0][i]
                })
        return formatted

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return Chroma collection statistics for UI"""
        try:
            count = self.collection.count()
            stats = {
                "total_documents": count,
                "collection_name": Config.COLLECTION_NAME,
                "db_path": str(Config.CHROMA_DB_PATH),
            }

            if count > 0:
                sample = self.collection.get(limit=min(count, 100))
                video_ids = {m.get("video_id") for m in sample["metadatas"] if "video_id" in m}
                stats["unique_videos"] = len(video_ids)
                stats["video_ids"] = list(video_ids)
            else:
                stats["unique_videos"] = 0
                stats["video_ids"] = []

            return stats
        except Exception as e:
            print(f"⚠️ Could not fetch collection stats: {e}")
            return {
                "total_documents": 0,
                "collection_name": Config.COLLECTION_NAME,
                "db_path": str(Config.CHROMA_DB_PATH),
                "unique_videos": 0,
                "video_ids": []
            }

    def delete_video(self, video_id: str) -> int:
        """Delete all chunks belonging to a given YouTube video"""
        results = self.collection.get(where={"video_id": video_id})
        if results['ids']:
            self.collection.delete(ids=results['ids'])
            count = len(results['ids'])
            print(f"🗑 Deleted {count} docs for video: {video_id}")
            return count
        print(f"No docs found for {video_id}")
        return 0

    def reset_collection(self):
        """Completely reset collection"""
        self.client.delete_collection(name=Config.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=Config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "dimension": 384}
        )
        print("🔄 Collection reset successfully")
