import gradio as gr
from chatbot import YouTubeChatbot
from typing import List, Tuple
import traceback
from db_cleanup import DBCleanupManager
from config import Config

class GradioApp:
    """Gradio web interface for YouTube RAG Chatbot"""
    
    def __init__(self):
        """Initialize chatbot and cleanup manager"""
        self.chatbot = YouTubeChatbot()
        self.cleanup_manager = DBCleanupManager(
            Config.BASE_DB_DIR,
            Config.RUN_ID
        )
    
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
    
    def get_storage_stats_ui(self) -> str:
        """Get storage statistics for UI"""
        try:
            stats = self.cleanup_manager.get_storage_stats()
            
            output = f"""📊 **Database Storage Statistics**

📁 Total Runs: {stats['total_runs']}
💾 Total Size: {stats['total_size_human']}
🔄 Current Run: {stats['current_run']}

"""
            
            if stats['runs']:
                output += "**All Runs:**\n\n"
                output += "| Run ID | Size | Age | Status |\n"
                output += "|--------|------|-----|--------|\n"
                
                for run in stats['runs']:
                    current_marker = "⭐ CURRENT" if run['is_current'] else ""
                    age_str = f"{run['age_days']:.1f} days"
                    output += f"| `{run['run_id']}` | {run['size_human']} | {age_str} | {current_marker} |\n"
            else:
                output += "*No database runs found.*\n"
            
            output += f"\n**Retention Policy:** {Config.CLEANUP_RETENTION_MODE}\n"
            output += f"- Keep runs from last {Config.CLEANUP_RETENTION_DAYS} days\n"
            output += f"- Keep last {Config.CLEANUP_RETENTION_COUNT} runs\n"
            
            return output
            
        except Exception as e:
            return f"❌ Error fetching storage stats: {str(e)}\n\n{traceback.format_exc()}"
    
    def cleanup_preview_ui(self) -> str:
        """Preview what will be deleted"""
        try:
            result = self.cleanup_manager.cleanup_old_runs(dry_run=True)
            
            if result['deleted_count'] == 0:
                return "✅ No runs to delete based on current retention policy.\n\nAll runs are within the retention period."
            
            output = f"""🧹 **Cleanup Preview**

Will delete **{result['deleted_count']} run(s)**:

"""
            for run_id in result['deleted_runs']:
                output += f"  • `{run_id}`\n"
            
            output += f"\n💾 **Space to be freed:** {result['space_freed_human']}\n"
            output += "\n⚠️ Click 'Confirm Cleanup' below to proceed with deletion."
            
            return output
            
        except Exception as e:
            return f"❌ Error previewing cleanup: {str(e)}\n\n{traceback.format_exc()}"
    
    def cleanup_execute_ui(self, progress=gr.Progress()) -> str:
        """Execute cleanup"""
        try:
            progress(0, desc="Starting cleanup...")
            
            # First check if there's anything to delete
            preview = self.cleanup_manager.cleanup_old_runs(dry_run=True)
            if preview['deleted_count'] == 0:
                return "✅ No runs to delete. All runs are within retention policy."
            
            progress(0.3, desc=f"Deleting {preview['deleted_count']} run(s)...")
            
            # Execute cleanup
            result = self.cleanup_manager.cleanup_old_runs(dry_run=False)
            
            progress(1.0, desc="Complete!")
            
            output = f"""✅ **Cleanup Complete!**

📊 Deleted: {result['deleted_count']} run(s)
💾 Space freed: {result['space_freed_human']}

"""
            
            if result['deleted_runs']:
                output += "**Deleted runs:**\n"
                for run_id in result['deleted_runs']:
                    output += f"  • `{run_id}`\n"
            
            if result['errors']:
                output += f"\n⚠️ **Errors encountered:** {len(result['errors'])}\n"
                for error in result['errors']:
                    output += f"  • `{error['run_id']}`: {error['error']}\n"
            
            return output
            
        except Exception as e:
            return f"❌ Error during cleanup: {str(e)}\n\n{traceback.format_exc()}"
    
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
                
                # Tab 4: Cleanup
                with gr.Tab("🧹 Cleanup"):
                    gr.Markdown("### Database Storage Management")
                    
                    gr.Markdown(
                        """
                        Manage old database runs to free up disk space. Each application run creates a new 
                        timestamped database folder. Use this tab to view storage usage and clean up old runs.
                        """
                    )
                    
                    # Storage Stats Section
                    with gr.Group():
                        gr.Markdown("#### 📊 Storage Statistics")
                        storage_stats_output = gr.Markdown()
                        refresh_storage_btn = gr.Button("🔄 Refresh Storage Stats")
                    
                    gr.Markdown("---")
                    
                    # Cleanup Section
                    with gr.Group():
                        gr.Markdown("#### 🧹 Cleanup Old Runs")
                        
                        cleanup_preview_output = gr.Markdown()
                        
                        with gr.Row():
                            preview_cleanup_btn = gr.Button("👁️ Preview Cleanup", variant="secondary")
                            execute_cleanup_btn = gr.Button("✅ Confirm Cleanup", variant="primary")
                        
                        cleanup_result_output = gr.Markdown()
                    
                    gr.Markdown(
                        """
                        **How it works:**
                        1. Click "Preview Cleanup" to see what will be deleted
                        2. Review the list of runs to be deleted
                        3. Click "Confirm Cleanup" to proceed with deletion
                        
                        **Retention Policy:**
                        - The current run is always protected
                        - Runs are kept based on configured retention settings
                        - See CLEANUP.md for configuration details
                        """
                    )
                    
                    # Button actions
                    refresh_storage_btn.click(
                        fn=self.get_storage_stats_ui,
                        outputs=[storage_stats_output]
                    )
                    
                    preview_cleanup_btn.click(
                        fn=self.cleanup_preview_ui,
                        outputs=[cleanup_preview_output]
                    )
                    
                    execute_cleanup_btn.click(
                        fn=self.cleanup_execute_ui,
                        outputs=[cleanup_result_output]
                    )
                    
                    # Load storage stats on tab open
                    demo.load(
                        fn=self.get_storage_stats_ui,
                        outputs=[storage_stats_output]
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