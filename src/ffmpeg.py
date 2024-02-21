import subprocess
import os
from typing import List
from threading import Thread


class FFMpeg:
    def __init__(self):
        pass

    @staticmethod
    def combine_audio_with_image(image_path: str, audio_path: str, output_path: str):
        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # Ensure dimensions are divisible by 2
            "-profile:v", "high",  # Use high profile
            "-level", "4.0",  # Use level 4.0
            "-preset", "fast",  # Use fast preset for speed
            "-crf", "23",  # Adjust CRF (Constant Rate Factor) for quality vs. size tradeoff
            "-pix_fmt", "yuv420p",  # Use YUV 4:2:0 pixel format for wider compatibility
            "-c:a", "aac",
            "-strict", "experimental",
            "-shortest",
            output_path
        ]
        subprocess.run(ffmpeg_command)

    @staticmethod
    def combine_audio_with_image_multi(slides: List[str], audios: List[str], output_folder="dir") -> List[str]:
        """
        Create a video for each slide and audio pair.

        Args:
            slides (List[str]): List of paths to slide images.
            audios (List[str]): List of paths to audio files.
            output_folder (str): Folder where the output videos will be saved.
        Returns:
            List[str]: List of paths to the generated videos.
        """
        video_paths = []
        threads = []

        for i, (slide, audio) in enumerate(zip(slides, audios)):
            output_path = f"{output_folder}/video_{i}.mp4"
            thread = Thread(target=FFMpeg.combine_audio_with_image, args=[slide, audio, output_path])
            threads.append(thread)
            video_paths.append(output_path)
            thread.start()

        for thread in threads:
            thread.join()

        return video_paths

    @staticmethod
    def concatenate_videos(input_files, output_path):
        # Write a temporary file listing input files
        with open('input_files.txt', 'w') as f:
            for file in input_files:
                f.write(f"file '{file}'\n")

        # Run ffmpeg to concatenate videos
        subprocess.run([
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-f", "concat",  # Use concat demuxer
            "-safe", "0",  # Allow input file paths to be interpreted as relative paths
            "-i", "input_files.txt",  # Input file listing
            "-c", "copy",  # Use copy codec for fast concatenation
            output_path
        ])

        # Delete the temporary file
        os.remove('input_files.txt')

    @staticmethod
    def extract_audio_from_video(video_path: str, output_path="dir/audio.mp3"):
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vn",  # Disable video recording
            "-acodec", "libmp3lame",  # Use MP3 codec
            output_path
        ])
        return output_path

    @staticmethod
    def render_subtitles(video_path: str, srt_path: str, output_path: str):
        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-vf", f"subtitles='{srt_path}'",  # Apply subtitles filter
            "-c:a", "copy",  # Copy audio stream
            "-c:v", "libx264",  # Video codec
            "-crf", "20",  # Constant Rate Factor (quality)
            "-preset", "medium",  # Preset for encoding speed
            "-y",  # Overwrite output file if it exists
            output_path
        ])
