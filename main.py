from utils import read_video, save_video
from trackers import Tracker

def main():
    #Baca video
    video_frames = read_video('input_videos/08fd33_4.mp4')

    #inisialisasi tracker
    tracker = Tracker('models/best.pt')

    tracks = tracker.get_object_tracks(video_frames)

    #Simpan video
    save_video(video_frames, 'output_videos/output_video.avi')

if __name__ == '__main__':
    main() 