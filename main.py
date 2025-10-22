import sys
import argparse
from chatbot import YouTubeChatbot
from typing import List

def main():
    """Main entry point for YouTube RAG Chatbot CLI"""
    
    parser = argparse.ArgumentParser(
        description="YouTube RAG Chatbot - Ask questions about YouTube videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a video and start chatting
  python main.py --add https://www.youtube.com/watch?v=VIDEO_ID
  
  # Add multiple videos
  python main.py --add URL1 URL2 URL3
  
  # Start chat with existing knowledge base
  python main.py --chat
  
  # Show statistics
  python main.py --stats
  
  # Reset knowledge base
  python main.py --reset
  
  # Launch Gradio web UI
  python main.py --ui
        """
    )
    
    parser.add_argument(
        '--add',
        nargs='+',
        metavar='URL',
        help='Add YouTube video(s) to knowledge base'
    )
    
    parser.add_argument(
        '--chat',
        action='store_true',
        help='Start interactive chat session'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show knowledge base statistics'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset the entire knowledge base'
    )
    
    parser.add_argument(
        '--delete',
        metavar='VIDEO_ID',
        help='Delete a specific video from knowledge base'
    )
    
    parser.add_argument(
        '--ui',
        action='store_true',
        help='Launch Gradio web interface'
    )
    
    parser.add_argument(
        '--share',
        action='store_true',
        help='Create public link for Gradio UI (use with --ui)'
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    try:
        # Initialize chatbot
        chatbot = YouTubeChatbot()
        
        # Handle different commands
        if args.ui:
            # Launch Gradio UI
            from app import GradioApp
            app = GradioApp()
            app.launch(share=args.share)
            return
        
        if args.add:
            # Add videos
            print(f"\n{'='*80}")
            print(f"ADDING {len(args.add)} VIDEO(S)")
            print(f"{'='*80}\n")
            
            chatbot.add_multiple_videos(args.add)
            
            # Ask if user wants to chat
            response = input("\nWould you like to start chatting? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                chatbot.chat_loop()
            return
        
        if args.stats:
            # Show statistics
            stats = chatbot.get_stats()
            print("\n" + "="*80)
            print("KNOWLEDGE BASE STATISTICS")
            print("="*80)
            print(f"\n📚 Total Documents: {stats['total_documents']}")
            print(f"🎥 Unique Videos: {stats.get('unique_videos', 0)}")
            print(f"💾 Database Path: {stats['db_path']}")
            print(f"📦 Collection: {stats['collection_name']}")
            
            if stats.get('video_ids'):
                print(f"\n🎬 Video IDs:")
                for vid_id in stats['video_ids']:
                    print(f"   • {vid_id}")
            
            print("\n" + "="*80 + "\n")
            return
        
        if args.delete:
            # Delete video
            confirm = input(f"\nAre you sure you want to delete video '{args.delete}'? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                count = chatbot.delete_video(args.delete)
                if count > 0:
                    print(f"\n✅ Deleted {count} chunks for video: {args.delete}\n")
                else:
                    print(f"\n❌ Video not found: {args.delete}\n")
            else:
                print("\n❌ Deletion cancelled\n")
            return
        
        if args.reset:
            # Reset knowledge base
            confirm = input("\n⚠️  Are you sure you want to reset the entire knowledge base? This cannot be undone. (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                chatbot.reset()
                print("\n✅ Knowledge base reset successfully\n")
            else:
                print("\n❌ Reset cancelled\n")
            return
        
        if args.chat:
            # Start chat loop
            chatbot.chat_loop()
            return
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()