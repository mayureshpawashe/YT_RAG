from youtube_loader import YouTubeLoader
from text_processor import TextProcessor
from vector_store import VectorStore
from rag_engine import RAGEngine
from config import Config
from typing import List

class YouTubeChatbot:
    """Main chatbot class orchestrating all components"""
    
    def __init__(self):
        """Initialize all components"""
        print("\n" + "="*80)
        print("INITIALIZING YOUTUBE RAG CHATBOT")
        print("="*80 + "\n")
        
        self.youtube_loader = YouTubeLoader()
        self.text_processor = TextProcessor()
        self.vector_store = VectorStore()
        self.rag_engine = RAGEngine()
        
        print("\n" + "="*80)
        print("CHATBOT READY!")
        print("="*80 + "\n")
    
    def add_video(self, video_url: str) -> dict:
        """
        Add a YouTube video to the knowledge base
        
        Args:
            video_url: YouTube video URL or ID
            
        Returns:
            Dictionary with status and statistics
        """
        try:
            print(f"\n📥 Processing video: {video_url}")
            print("-" * 80)
            
            # Step 1: Get transcript
            video_data = self.youtube_loader.get_transcript(video_url)
            video_id = video_data['video_id']
            
            # Step 2: Save transcript
            self.youtube_loader.save_transcript(video_data)
            
            # Step 3: Split into chunks
            documents = self.text_processor.split_text(
                text=video_data['transcript'],
                metadata={
                    'video_id': video_id,
                    'url': video_data['url'],
                    "title": video_data["title"],
                }
            )
            
            # Step 4: Get chunk statistics
            stats = self.text_processor.get_chunk_stats(documents)
            print(f"\nChunk Statistics:")
            print(f"  Total chunks: {stats['total_chunks']}")
            print(f"  Avg size: {stats['avg_chunk_size']:.0f} chars")
            print(f"  Min/Max: {stats['min_chunk_size']}/{stats['max_chunk_size']} chars")
            
            # Step 5: Add to vector store
            num_added = self.vector_store.add_documents(documents, video_id)
            
            print(f"\n✅ Video processed successfully!")
            print(f"   Video ID: {video_id}")
            print(f"   Chunks added: {num_added}")
            print("-" * 80)
            
            return {
                'success': True,
                'video_id': video_id,
                'url': video_data['url'],
                'chunks_added': num_added,
                'stats': stats
            }
            
        except Exception as e:
            print(f"\n❌ Error processing video: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_multiple_videos(self, video_urls: List[str]) -> List[dict]:
        """
        Add multiple videos to the knowledge base
        
        Args:
            video_urls: List of YouTube video URLs
            
        Returns:
            List of results for each video
        """
        results = []
        
        for i, url in enumerate(video_urls, 1):
            print(f"\n{'='*80}")
            print(f"PROCESSING VIDEO {i}/{len(video_urls)}")
            print(f"{'='*80}")
            
            result = self.add_video(url)
            results.append(result)
        
        # Summary
        successful = sum(1 for r in results if r.get('success'))
        print(f"\n{'='*80}")
        print(f"SUMMARY: {successful}/{len(video_urls)} videos processed successfully")
        print(f"{'='*80}\n")
        
        return results
    
    def ask(self, question: str, show_sources: bool = False) -> str:
        """
        Ask a question to the chatbot
        
        Args:
            question: User question
            show_sources: Whether to display sources
            
        Returns:
            Answer string
        """
        result = self.rag_engine.query(question, include_sources=show_sources)
        
        answer = result['answer']
        
        if show_sources and result.get('sources'):
            answer += "\n\n📚 Sources:\n"
            for source in result['sources']:
                answer += f"\n{source['source_number']}. Video: {source['video_id']} "
                answer += f"(Similarity: {source['similarity']:.2%})\n"
                answer += f"   URL: {source['url']}\n"
        
        return answer
    
    def get_stats(self) -> dict:
        """Get statistics about the knowledge base"""
        return self.vector_store.get_collection_stats()
    
    def delete_video(self, video_id: str) -> int:
        """Delete a video from knowledge base"""
        return self.vector_store.delete_video(video_id)
    
    def reset(self):
        """Reset the entire knowledge base"""
        self.vector_store.reset_collection()
    
    def chat_loop(self):
        """Interactive chat loop in terminal"""
        print("\n" + "="*80)
        print("YOUTUBE RAG CHATBOT - Interactive Mode")
        print("="*80)
        print("\nCommands:")
        print("  - Type your question to get answers")
        print("  - Type 'stats' to see knowledge base statistics")
        print("  - Type 'exit' or 'quit' to end the conversation")
        print("="*80 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\n👋 Goodbye! Thanks for chatting!\n")
                    break
                
                if user_input.lower() == 'stats':
                    stats = self.get_stats()
                    print(f"\n📊 Knowledge Base Statistics:")
                    print(f"   Total documents: {stats['total_documents']}")
                    print(f"   Unique videos: {stats.get('unique_videos', 0)}")
                    if stats.get('video_ids'):
                        print(f"   Video IDs: {', '.join(stats['video_ids'])}")
                    print()
                    continue
                
                # Get answer
                print("\n🤖 Assistant: ", end="", flush=True)
                answer = self.ask(user_input, show_sources=True)
                print(answer + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for chatting!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")