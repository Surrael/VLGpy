import json
import warnings
from typing import Iterator, TextIO
from openai import OpenAI


class SubtitleGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_subtitles(self, audio_path: str, srt_path="dir/subtitles.srt"):
        print(f"Generating subtitles...")

        warnings.filterwarnings("ignore")
        result = json.loads(self.transcribe(audio_path))
        warnings.filterwarnings("default")

        with open(srt_path, "w", encoding="utf-8") as srt:
            self.write_srt(result["segments"], file=srt)

        return srt_path

    @staticmethod
    def format_timestamp(seconds: float, always_include_hours: bool = False):
        assert seconds >= 0, "non-negative timestamp expected"
        milliseconds = round(seconds * 1000.0)

        hours = milliseconds // 3_600_000
        milliseconds -= hours * 3_600_000

        minutes = milliseconds // 60_000
        milliseconds -= minutes * 60_000

        seconds = milliseconds // 1_000
        milliseconds -= seconds * 1_000

        hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
        return f"{hours_marker}{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    @staticmethod
    def write_srt(transcript: Iterator[dict], file: TextIO):
        for i, segment in enumerate(transcript, start=1):
            print(
                f"{i}\n"
                f"{SubtitleGenerator.format_timestamp(segment['start'], always_include_hours=True)} --> "
                f"{SubtitleGenerator.format_timestamp(segment['end'], always_include_hours=True)}\n"
                f"{segment['text'].strip().replace('-->', '->')}\n",
                file=file,
                flush=True,
            )

    def transcribe(self, path: str):
        audio_file = open(path, "rb")
        transcript = self.client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
        return transcript.model_dump_json()


