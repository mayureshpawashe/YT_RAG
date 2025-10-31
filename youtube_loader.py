import os
import re
from typing import Optional, Dict
from youtube_transcript_api import YouTubeTranscriptApi
from config import Config
import requests

class YouTubeLoader:
    """Load and process YouTube video transcripts using youtube-transcript-api"""
    
    def __init__(self):
        """Initialize the loader and set transcripts directory"""
        self.transcripts_dir = Config.TRANSCRIPTS_DIR
        print("✓ YouTubeLoader initialized (using youtube-transcript-api)")
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
            r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Assume it's a video ID if it's an 11-char string
        if len(url) == 11:
            return url
        
        return None

    def fetch_video_title(self, video_id: str) -> str:
            try:
                resp = requests.get(
                    "https://www.youtube.com/oembed",
                    params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
                    timeout=10,
                )
                resp.raise_for_status()
                return resp.json().get("title", video_id)
            except Exception as exc:
                print(f"⚠️ Could not fetch title for {video_id}: {exc}")
                return video_id

    def get_transcript(self, video_url: str, languages: list = None) -> dict:
        """
        Fetch video transcript using youtube-transcript-api
        
        Args:
            video_url: YouTube video URL or ID
            languages: List of preferred language codes (e.g., ['en'])
            
        Returns:
            Dictionary with video data
        """
        if languages is None:
            languages = ['en']
            
        video_id = self.extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {video_url}")
        
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            
            # Find a transcript in the preferred languages
            transcript = None
            try:
                transcript = transcript_list.find_transcript(languages)
            except Exception:
                # If exact match not found, try finding a generated one
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                except Exception as e:
                    available_langs = [t.language_code for t in transcript_list]
                    raise Exception(f"No transcript found in {languages}. Available: {available_langs}") from e

            # Fetch the full transcript data
            transcript_data = transcript.fetch()
            title = self.fetch_video_title(video_id)
            
            # --- THIS IS THE FIX ---
            # Changed segment['text'] to segment.text
            full_transcript = " ".join([segment.text for segment in transcript_data])
            # --- END OF FIX ---
            
            result = {
                'video_id': video_id,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'title': title,  
                'transcript': full_transcript,
                'language': transcript.language_code
            }
            
            print(f"✓ Successfully fetched transcript for: {video_id}")
            print(f"  Language: {result['language']}")
            print(f"  Transcript length: {len(full_transcript)} characters")
            
            return result
            
        except Exception as e:
            raise Exception(f"Error processing video {video_id}: {str(e)}")
        
    


    def save_transcript(self, video_data: dict):
        """Save transcript to a text file"""
        if not video_data.get('video_id') or not video_data.get('transcript'):
            print("! Invalid video data for saving")
            return
        
        file_path = os.path.join(self.transcripts_dir, f"{video_data['video_id']}.txt")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Use video_id as title since we don't fetch the real title
                f.write(f"Title: {video_data.get('title', video_data['video_id'])}\n") 
                f.write(f"URL: {video_data.get('url', 'N/A')}\n")
                f.write(f"Language: {video_data.get('language', 'N/A')}\n")
                f.write(f"{'='*30}\n\n")
                f.write(video_data['transcript'])
            
            print(f"✓ Transcript saved to: {file_path}")
            
        except Exception as e:
            print(f"! Error saving transcript: {str(e)}")