from groq import Groq
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Union
from config import Config

class LLMWrapper:
    """Wrapper for LLM and embedding models"""
    
    def __init__(self):
        # Initialize Groq
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        
        print(f"✓ LLM initialized (using Groq {Config.LLM_MODEL})")
        print(f"✓ Embeddings initialized (using {Config.EMBEDDING_MODEL})")
    
    def get_completion(self, messages: List[Dict[str, str]], stream: bool = True) -> str:
        """Get completion from Groq"""
        try:
            completion = self.groq_client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=messages,
                temperature=Config.TEMPERATURE,
                max_completion_tokens=Config.MAX_TOKENS,
                top_p=1,
                reasoning_effort=Config.REASONING_EFFORT,
                stream=stream,
                stop=None
            )
            
            if stream:
                full_response = ""
                for chunk in completion:
                    content = chunk.choices[0].delta.content or ""
                    full_response += content
                    print(content, end="", flush=True)
                return full_response
            else:
                return completion.choices[0].message.content
                
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")
    
    def get_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Get embeddings using SentenceTransformer"""
        try:
            if isinstance(texts, str):
                texts = [texts]
            embeddings = self.embedding_model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            raise Exception(f"Embedding error: {str(e)}")