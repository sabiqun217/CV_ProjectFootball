import gradio as gr
import os
import time
import shutil
from main import process_video_core

def process_with_file_serving(video_file):
    """
    Process video dan serve file dengan cara yang lebih reliable
    """
    if video_file is None:
        return None, "❌ Please upload a video file", ""
    
    try:
        print(f"📹 Processing video: {video_file}")
        
        # Process video
        output_path = process_video_core(video_file)
        
        # Create public directory yang bisa diakses web server
        public_dir = "public_outputs"
        os.makedirs(public_dir, exist_ok=True)
        
        # Copy dengan nama yang web-friendly
        timestamp = int(time.time())
        public_filename = f"football_analysis_{timestamp}.mp4"
        public_path = os.path.join(public_dir, public_filename)
        
        shutil.copy2(output_path, public_path)
        
        # Verify file
        if os.path.exists(public_path):
            file_size = os.path.getsize(public_path)
            print(f"✅ File ready: {public_path} ({file_size} bytes)")
            
            return public_path, f"✅ Analysis completed successfully! File size: {file_size:,} bytes", public_path
        else:
            return None, "❌ Failed to create output file", ""
            
    except Exception as e:
        error_msg = f"❌ Processing failed: {str(e)}"
        print(error_msg)
        return None, error_msg, ""

# Create Gradio Blocks interface
with gr.Blocks(
    title="Football Analysis System",
    theme=gr.themes.Soft(),
    css="""
    .gradio-container {
        max-width: 1400px !important;
    }
    .output-video {
        height: 500px !important;
    }
    """
) as demo:
    
    gr.Markdown("""
    # ⚽ Football Match Analysis System
    
    Upload a football match video to get comprehensive analysis including player tracking, 
    team assignment, speed calculation, and ball possession analysis.
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📤 Input")
            video_input = gr.Video(
                label="Upload Match Video",
                height=400
            )
            
            analyze_btn = gr.Button(
                "🎯 Analyze Video",
                variant="primary",
                size="lg"
            )
            
            status_text = gr.Textbox(
                label="Status",
                value="Ready to analyze...",
                interactive=False,
                max_lines=3
            )
            
        with gr.Column(scale=1):
            gr.Markdown("### 📥 Output")
            video_output = gr.Video(
                label="Analysis Result",
                height=400,
                elem_classes=["output-video"]
            )
            
            download_file = gr.File(
                label="Download Result",
                visible=True
            )
    
    # Event handler
    analyze_btn.click(
        fn=process_with_file_serving,
        inputs=[video_input],
        outputs=[video_output, status_text, download_file],
        show_progress=True
    )
    
    gr.Markdown("""
    ### 📋 Instructions:
    1. **Upload** your football match video (MP4, AVI, MOV supported)
    2. **Click** "Analyze Video" and wait for processing
    3. **Watch** the result in the output player
    4. **Download** the processed video using the download link
    
    ### ✨ Features:
    - 🎯 **Player Detection**: Automatic detection and tracking of all players
    - 👕 **Team Assignment**: Identifies teams based on jersey colors
    - ⚽ **Ball Tracking**: Tracks ball position and possession
    - 📊 **Statistics**: Speed, distance, and possession analytics
    - 📷 **Camera Compensation**: Adjusts for camera movement
    """)

if __name__ == "__main__":
    import sys
    import asyncio
    
    # Setup for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    if len(sys.argv) > 1 and sys.argv[1] == "nogradio":
        from main import main
        main()
    else:
        # Create necessary directories
        os.makedirs("public_outputs", exist_ok=True)
        
        print("🚀 Starting Football Analysis System...")
        print("📂 Output files will be saved to: public_outputs/")
        
        # SOLUSI 1: Basic launch (paling simple)
        demo.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            inbrowser=True,
            show_error=True
        )
        
        # SOLUSI 2: Jika masih perlu file serving, gunakan cara alternatif
        # demo.launch(
        #     server_name="127.0.0.1",
        #     server_port=7860,
        #     share=False,
        #     inbrowser=True,
        #     show_error=True,
        #     allowed_paths=[".", "./public_outputs"]  # Alternatif untuk file serving
        # )                                                                                               