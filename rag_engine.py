from typing import List, Optional, Tuple
from llm_wrapper import LLMWrapper
from vector_store import VectorStore
from config import Config

class RAGEngine:
    """RAG (Retrieval-Augmented Generation) engine for question answering"""
    
    def __init__(self):
        """Initialize RAG engine with LLM and vector store"""
        self.llm = LLMWrapper()
        self.vector_store = VectorStore()
        
        # Define system prompt
        self.system_prompt = """You are a helpful AI assistant that answers questions based on YouTube video transcripts.

Instructions:
- Use the provided context from video transcripts to answer questions
- If the answer is not in the context, say "I don't have enough information from the video transcripts to answer that"
- Be concise but informative
- If relevant, mention which video the information comes from
- Maintain a friendly and conversational tone

Context from video transcripts:
{context}
"""
        
        print("✓ RAG Engine initialized")
    
    def retrieve_context(self, query: str, k: int = None) -> Tuple[str, List[dict]]:
        """Retrieve relevant context for a query"""
        results = self.vector_store.similarity_search(query, k=k)
        
        if not results:
            return "", []
        
        context_parts = []
        for i, result in enumerate(results, 1):
            video_id = result['metadata'].get('video_id', 'unknown')
            text = result['text']
            context_parts.append(f"[Source {i} - Video: {video_id}]\n{text}")
        
        formatted_context = "\n\n---\n\n".join(context_parts)
        return formatted_context, results
    
    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM"""
        messages = [
            {"role": "system", "content": self.system_prompt.format(context=context)},
            {"role": "user", "content": query}
        ]
        return self.llm.get_completion(messages)
    
    def query(self, question: str, include_sources: bool = True) -> dict:
        """Main query method - retrieve and generate answer"""
        stats = self.vector_store.get_collection_stats()
        if stats['total_documents'] == 0:
            return {
                'answer': "No video transcripts have been loaded yet. Please add some YouTube videos first.",
                'sources': []
            }
        
        context, sources = self.retrieve_context(question)
        
        if not context:
            return {
                'answer': "I couldn't find relevant information in the video transcripts to answer your question.",
                'sources': []
            }
        
        answer = self.generate_answer(question, context)
        result = {'answer': answer}
        
        if include_sources:
            formatted_sources = []
            for i, source in enumerate(sources, 1):
                formatted_sources.append({
                    'source_number': i,
                    'video_id': source['metadata'].get('video_id'),
                    'url': source['metadata'].get('source'),
                    'similarity': round(source['similarity'], 3),
                    'text_preview': source['text'][:200] + "..." if len(source['text']) > 200 else source['text']
                })
            result['sources'] = formatted_sources
        
        return result
    
    def chat(self, question: str) -> str:
        """Simple chat method that returns just the answer"""
        result = self.query(question, include_sources=False)
        return result['answer']