import subprocess
import os

def extract_frames_ffmpeg(input_video_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    command = [
        'ffmpeg',
        '-i', input_video_path,
        '-vf', 'fps=1',
        os.path.join(output_dir, 'frame_%03d.png')
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Frames extracted and saved to {output_dir} at one frame per second")
        # Assuming the duration of the video is not known, 
        # and thus the exact number of frames to be extracted is not known beforehand.
        # Listing the directory content to return the paths of extracted frames.
        extracted_frames = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if str(f).startswith('frame_')]
        return extracted_frames
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return []