from utils import read_video, save_video
from trackers import Tracker
import cv2
import numpy as np
from team_assigner import TeamAssigner
from player_ball_assigner import PlayerBallAssigner
from camera_movement_estimator import CameraMovementEstimator
from view_transformer import ViewTransformer
from speed_and_distance_estimator import SpeedAndDistance_Estimator
import gradio as gr
import os
import tempfile
import shutil
import logging
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def save_video_for_gradio(output_video_frames, output_video_path):
    """
    Save video dengan format yang kompatibel untuk Gradio
    """
    if not output_video_frames:
        raise ValueError("No frames to save")
    
    frame_height, frame_width = output_video_frames[0].shape[:2]
    fps = 24
    
    # Try multiple codec options for better compatibility
    codecs_to_try = [
        ('mp4v', '.mp4'),
        ('XVID', '.avi'),
        ('MJPG', '.avi')
    ]
    
    for codec, ext in codecs_to_try:
        try:
            # Adjust extension based on codec
            base_path = os.path.splitext(output_video_path)[0]
            current_path = base_path + ext
            
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(current_path, fourcc, fps, (frame_width, frame_height))
            
            if not out.isOpened():
                logger.warning(f"Could not open VideoWriter with {codec}")
                continue
            
            # Write all frames
            for i, frame in enumerate(output_video_frames):
                if frame is not None:
                    # Ensure frame is in correct format (BGR for OpenCV)
                    if len(frame.shape) == 3:
                        out.write(frame)
                    if i % 100 == 0:  # Progress indicator
                        logger.info(f"Writing frame {i}/{len(output_video_frames)}")
            
            out.release()
            
            # Verify file was created successfully
            if os.path.exists(current_path) and os.path.getsize(current_path) > 10000:  # At least 10KB
                logger.info(f"Video saved successfully: {current_path} ({os.path.getsize(current_path)} bytes)")
                return current_path
            else:
                logger.warning(f"Video file too small or empty with {codec}")
                
        except Exception as e:
            logger.error(f"Error with {codec}: {e}")
            continue
    
    raise Exception("Failed to save video with any available codec")

def process_video_gradio(input_video):
    """
    Enhanced Gradio processing function with better file handling
    """
    if input_video is None:
        return None, "Please upload a video file"
    
    logger.info("🎯 Starting video analysis...")
    
    try:
        # Process the video
        processed_path = process_video_core(input_video)
        
        # Create a web-accessible copy for Gradio
        # Use a predictable filename in a web-accessible directory
        output_dir = "gradio_outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        import time
        timestamp = int(time.time())
        web_accessible_path = os.path.join(output_dir, f"result_{timestamp}.mp4")
        
        # Copy and ensure it's accessible
        shutil.copy2(processed_path, web_accessible_path)
        
        # Verify the copy
        if os.path.exists(web_accessible_path) and os.path.getsize(web_accessible_path) > 0:
            logger.info(f"✅ Video ready for display: {web_accessible_path}")
            return web_accessible_path, f"Analysis completed! File saved as: {os.path.basename(web_accessible_path)}"
        else:
            raise Exception("Failed to create web-accessible copy")
            
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return None, error_msg

def process_video_core(input_video_path):
    """
    Core processing function
    """
    # Read Video
    logger.info("📹 Loading video...")
    video_frames = read_video(input_video_path)
    logger.info(f"   Loaded {len(video_frames)} frames")

    # Initialize Tracker
    logger.info("🎯 Initializing object tracker...")
    tracker = Tracker('models/best.pt')

    logger.info("🔍 Detecting players and ball...")
    tracks = tracker.get_object_tracks(video_frames,
                                       read_from_stub=False,
                                       stub_path='stubs/track_stubs.pkl')
    tracker.add_position_to_tracks(tracks)

    # Camera movement
    logger.info("📷 Estimating camera movement...")
    camera_movement_estimator = CameraMovementEstimator(video_frames[0])
    camera_movement_per_frame = camera_movement_estimator.get_camera_movement(
        video_frames,
        read_from_stub=True,
        stub_path='stubs/camera_movement_stub.pkl'
    )
    camera_movement_estimator.add_adjust_positions_to_tracks(tracks, camera_movement_per_frame)

    # View Transformer
    logger.info("🔄 Transforming field perspective...")
    view_transformer = ViewTransformer()
    view_transformer.add_transformed_position_to_tracks(tracks)

    # Interpolate Ball Positions
    logger.info("⚽ Interpolating ball positions...")
    tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])

    # Speed and distance
    logger.info("📊 Calculating speed and distance...")
    speed_and_distance_estimator = SpeedAndDistance_Estimator()
    speed_and_distance_estimator.add_speed_and_distance_to_tracks(tracks)

    # Assign Teams
    logger.info("👕 Assigning team colors...")
    team_assigner = TeamAssigner()
    team_assigner.assign_team_color(video_frames[0], tracks['players'][0])

    for frame_num, player_track in enumerate(tracks['players']):
        for player_id, track in player_track.items():
            team = team_assigner.get_player_team(video_frames[frame_num], track['bbox'], player_id)
            tracks['players'][frame_num][player_id]['team'] = team
            tracks['players'][frame_num][player_id]['team_color'] = team_assigner.team_colors[team]

    # Assign Ball
    logger.info("🏃 Analyzing ball possession...")
    player_assigner = PlayerBallAssigner()
    team_ball_control = []
    for frame_num, player_track in enumerate(tracks['players']):
        ball_bbox = tracks['ball'][frame_num][1]['bbox']
        assigned_player = player_assigner.assign_ball_to_player(player_track, ball_bbox)

        if assigned_player != -1:
            tracks['players'][frame_num][assigned_player]['has_ball'] = True
            team_ball_control.append(tracks['players'][frame_num][assigned_player]['team'])
        else:
            if len(team_ball_control) > 0:
                team_ball_control.append(team_ball_control[-1])
            else:
                team_ball_control.append(-1)
    team_ball_control = np.array(team_ball_control)

    # Draw Output
    logger.info("🎨 Creating annotated video...")
    output_video_frames = tracker.draw_annotations(video_frames, tracks, team_ball_control)
    output_video_frames = camera_movement_estimator.draw_camera_movement(output_video_frames, camera_movement_per_frame)
    speed_and_distance_estimator.draw_speed_and_distance(output_video_frames, tracks)

    # Save output
    output_dir = "output_videos"
    os.makedirs(output_dir, exist_ok=True)
    
    import time
    timestamp = int(time.time())
    output_path = os.path.join(output_dir, f"analysis_{timestamp}.mp4")
    
    logger.info("💾 Saving analysis result...")
    final_path = save_video_for_gradio(output_video_frames, output_path)
    
    return final_path

def create_interface():
    """
    Create Gradio interface with better output handling
    """
    with gr.Blocks(
        title="Football Analysis System",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1400px !important;
        }
        .video-container {
            min-height: 400px;
        }
        """
    ) as demo:
        
        gr.Markdown("""
        # ⚽ Football Match Analysis System
        
        Upload a football match video for automatic analysis including player tracking, 
        team identification, speed calculation, and ball possession analysis.
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                video_input = gr.Video(
                    label="📹 Upload Football Match Video",
                    height=400
                )
                
                analyze_btn = gr.Button(
                    "🎯 Analyze Video",
                    variant="primary",
                    size="lg"
                )
                
            with gr.Column(scale=1):
                video_output = gr.Video(
                    label="🎯 Analysis Result",
                    height=400,
                    elem_classes=["video-container"]
                )
                
                status_output = gr.Textbox(
                    label="📋 Status",
                    value="Ready to analyze video...",
                    interactive=False,
                    max_lines=3
                )
        
        # Event handler
        analyze_btn.click(
            fn=process_video_gradio,
            inputs=[video_input],
            outputs=[video_output, status_output],
            show_progress=True
        )
        
        gr.Markdown("""
        ### 📝 Instructions:
        1. Upload a football match video (MP4, AVI, MOV supported)
        2. Click "Analyze Video" and wait for processing
        3. The analyzed video will appear in the result panel
        4. You can download the result or find it in the `gradio_outputs/` folder
        
        ### 🔧 Features:
        - Player and ball detection & tracking
        - Team identification by jersey colors
        - Speed and distance calculations
        - Ball possession analysis
        - Camera movement compensation
        """)
    
    return demo

def main():
    """Debug function"""
    try:
        result = process_video_core('input_videos/test (18).mp4')
        print(f"✅ Processing completed: {result}")
    except Exception as e:
        print(f"❌ Processing failed: {e}")

if __name__ == '__main__':
    import sys
    import asyncio
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    if len(sys.argv) > 1 and sys.argv[1] == "nogradio":
        main()
    else:
        try:
            print("🚀 Launching Football Analysis System...")
            demo = create_interface()
            demo.launch(
                server_name="127.0.0.1",
                server_port=7860,
                share=False,
                inbrowser=True,
                show_error=True,
                debug=False
            )
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        except Exception as e:
            print(f"Launch failed: {e}")
            print("Try: python main.py nogradio")