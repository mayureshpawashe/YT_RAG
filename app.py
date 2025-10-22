import gradio as gr
from chatbot import YouTubeChatbot
from typing import List, Tuple
import traceback

class GradioApp:
    """Gradio web interface for YouTube RAG Chatbot"""
    
    def __init__(self):
        """Initialize chatbot"""
        self.chatbot = YouTubeChatbot()
    
    def add_video_ui(self, video_url: str, progress=gr.Progress()) -> str:
        """
        Add video through Gradio UI
        
        Args:
            video_url: YouTube video URL
            progress: Gradio progress tracker
            
        Returns:
            Status message
        """
        if not video_url or not video_url.strip():
            return "❌ Please enter a valid YouTube URL"
        
        try:
            progress(0, desc="Starting...")
            
            progress(0.2, desc="Fetching transcript...")
            result = self.chatbot.add_video(video_url)
            
            if result['success']:
                progress(1.0, desc="Complete!")
                return f"""✅ Video added successfully!
                
📹 Video ID: {result['video_id']}
📊 Chunks created: {result['chunks_added']}
📝 Total characters: {result['stats']['total_characters']}

You can now ask questions about this video!"""
            else:
                return f"❌ Error: {result['error']}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
    
    def chat_interface(self, message: str, history: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], str]:
        """
        Handle chat messages
        
        Args:
            message: User message
            history: Chat history
            
        Returns:
            Updated history and empty string for input
        """
        if not message or not message.strip():
            return history, ""
        
        try:
            # Get answer from chatbot
            response = self.chatbot.ask(message, show_sources=True)
            
            # Update history
            history.append((message, response))
            
            return history, ""
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            history.append((message, error_msg))
            return history, ""
    
    def get_stats_ui(self) -> str:
        """Get knowledge base statistics for UI"""
        try:
            stats = self.chatbot.get_stats()
            
            output = f"""📊 **Knowledge Base Statistics**

📚 Total Documents: {stats['total_documents']}
🎥 Unique Videos: {stats.get('unique_videos', 0)}
💾 Database Path: {stats['db_path']}
📦 Collection: {stats['collection_name']}
"""
            
            if stats.get('video_ids'):
                output += f"\n🎬 **Video IDs:**\n"
                for vid_id in stats['video_ids']:
                    output += f"  • {vid_id}\n"
            
            return output
            
        except Exception as e:
            return f"❌ Error fetching stats: {str(e)}"
    
    def clear_chat(self) -> Tuple[List, str]:
        """Clear chat history"""
        return [], ""
    
    def launch(self, share: bool = False):
        """Launch Gradio interface"""
        
        # Custom CSS
        custom_css = """
        .gradio-container {
            font-family: 'Arial', sans-serif;
        }
        .chat-message {
            padding: 10px;
            border-radius: 10px;
        }
        """
        
        # Create Gradio interface
        with gr.Blocks(css=custom_css, title="YouTube RAG Chatbot") as demo:
            
            gr.Markdown(
                """
                # 🤖 YouTube RAG Chatbot
                
                ### Ask questions about YouTube videos using AI!
                
                **How to use:**
                1. Add YouTube video URLs in the "Add Videos" tab
                2. Go to "Chat" tab and ask questions
                3. Check "Statistics" for knowledge base info
                """
            )
            
            with gr.Tabs():
                
                # Tab 1: Add Videos
                with gr.Tab("📥 Add Videos"):
                    gr.Markdown("### Add YouTube Videos to Knowledge Base")
                    
                    with gr.Row():
                        video_input = gr.Textbox(
                            label="YouTube Video URL",
                            placeholder="https://www.youtube.com/watch?v=...",
                            lines=1
                        )
                    
                    with gr.Row():
                        add_btn = gr.Button("Add Video", variant="primary")
                        clear_input_btn = gr.Button("Clear")
                    
                    video_output = gr.Textbox(
                        label="Status",
                        lines=8,
                        interactive=False
                    )
                    
                    # Button actions
                    add_btn.click(
                        fn=self.add_video_ui,
                        inputs=[video_input],
                        outputs=[video_output]
                    )
                    
                    clear_input_btn.click(
                        fn=lambda: "",
                        outputs=[video_input]
                    )
                    
                    gr.Markdown(
                        """
                        **Tips:**
                        - Videos must have English transcripts available
                        - Processing may take 30-60 seconds depending on video length
                        - You can add multiple videos one at a time
                        """
                    )
                
                # Tab 2: Chat
                with gr.Tab("💬 Chat"):
                    gr.Markdown("### Ask Questions About Your Videos")
                    
                    chatbot_ui = gr.Chatbot(
                        label="Conversation",
                        height=400,
                        type="tuples"  # Explicitly set to avoid warning
                    )
                    
                    with gr.Row():
                        msg_input = gr.Textbox(
                            label="Your Question",
                            placeholder="Ask a question about the videos...",
                            lines=2,
                            scale=4
                        )
                    
                    with gr.Row():
                        submit_btn = gr.Button("Send", variant="primary", scale=1)
                        clear_btn = gr.Button("Clear Chat", scale=1)
                    
                    # Chat actions
                    submit_btn.click(
                        fn=self.chat_interface,
                        inputs=[msg_input, chatbot_ui],
                        outputs=[chatbot_ui, msg_input]
                    )
                    
                    msg_input.submit(
                        fn=self.chat_interface,
                        inputs=[msg_input, chatbot_ui],
                        outputs=[chatbot_ui, msg_input]
                    )
                    
                    clear_btn.click(
                        fn=self.clear_chat,
                        outputs=[chatbot_ui, msg_input]
                    )
                    
                    gr.Markdown(
                        """
                        **Example Questions:**
                        - What is this video about?
                        - Summarize the main points
                        - What did they say about [topic]?
                        - Compare the information from different videos
                        """
                    )
                
                # Tab 3: Statistics
                with gr.Tab("📊 Statistics"):
                    gr.Markdown("### Knowledge Base Information")
                    
                    stats_output = gr.Markdown()
                    
                    refresh_btn = gr.Button("🔄 Refresh Statistics", variant="primary")
                    
                    refresh_btn.click(
                        fn=self.get_stats_ui,
                        outputs=[stats_output]
                    )
                    
                    # Load stats on tab open
                    demo.load(
                        fn=self.get_stats_ui,
                        outputs=[stats_output]
                    )
            
            gr.Markdown(
                """
                ---
                **Built with:** OpenAI GPT, ChromaDB, LangChain, Gradio
                """
            )
        
        print("\n" + "="*80)
        print("🚀 LAUNCHING GRADIO INTERFACE")
        print("="*80 + "\n")
        
        demo.launch(share=share, server_name="0.0.0.0", server_port=7860)


def main():
    """Main entry point for Gradio app"""
    try:
        app = GradioApp()
        app.launch(share=False)  # Set share=True to create public link
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error launching app: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()