import os
import sys

from PyQt5.QtCore import QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QVBoxLayout, QWidget, \
    QFileDialog, QCheckBox, QComboBox, QMessageBox, QHBoxLayout, QSizePolicy, QSpacerItem

import ffmpeg
import subtitle_generator
import util
import pyqtspinner

OPENAI_API_KEY = os.getenv("APIKEY")


class VideoGenerationThread(QThread):
    video_generated = pyqtSignal()

    def __init__(self, pdf_file, script_file, pptx_file, subtitles_enabled, selected_voice, video_name, video_location):
        super().__init__()
        self.pdf_file = pdf_file
        self.script_file = script_file
        self.pptx_file = pptx_file
        self.subtitles_enabled = subtitles_enabled
        self.selected_voice = selected_voice
        self.video_name = video_name
        self.video_location = video_location

    def run(self):
        slides = util.pdf_to_images(self.pdf_file)

        if self.script_file:
            script = util.parse_script_file(self.script_file)
        else:
            script = util.extract_pptx_notes(self.pptx_file)

        audios = util.text_to_speech(script, self.selected_voice, OPENAI_API_KEY)
        slide_videos = ffmpeg.FFMpeg.combine_audio_with_image_multi(slides, audios)
        if self.subtitles_enabled:
            ffmpeg.FFMpeg.concatenate_videos(slide_videos, "dir/concat.mp4")
            audio = ffmpeg.FFMpeg.extract_audio_from_video(f"{self.video_location}/{self.video_name}.mp4")
            subtitle_gen = subtitle_generator.SubtitleGenerator(OPENAI_API_KEY)
            srt = subtitle_gen.generate_subtitles(audio)
            ffmpeg.FFMpeg.render_subtitles("dir/concat.mp4",
                                           srt, f"{self.video_location}/{self.video_name}.mp4")
        else:
            ffmpeg.FFMpeg.concatenate_videos(slide_videos, f"{self.video_location}/{self.video_name}.mp4")

        self.video_generated.emit()


class DemoGenerationThread(QThread):
    video_generated = pyqtSignal()

    def __init__(self, pdf_file, script_file, pptx_file, video_name, video_location):
        super().__init__()
        self.pdf_file = pdf_file
        self.script_file = script_file
        self.pptx_file = pptx_file
        self.video_name = video_name
        self.video_location = video_location

    def run(self):
        slides = util.pdf_to_images(self.pdf_file)

        if self.script_file:
            script = util.parse_script_file(self.script_file)
        else:
            script = util.extract_pptx_notes(self.pptx_file)

        audios = util.text_to_speech_demo(script)
        slide_videos = ffmpeg.FFMpeg.combine_audio_with_image_multi(slides, audios)

        ffmpeg.FFMpeg.concatenate_videos(slide_videos, f"{self.video_location}/{self.video_name}.mp4")
        self.video_generated.emit()


class VideoGenerationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Lecture Generator")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon("res/icon.png"))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d30;
            }
            QPushButton {
                background-color: #55945d;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 16px;
                font-family: Segoe UI;
            }
            QPushButton:hover {
                background-color: #406645;
            }
            QLineEdit {
                color: #ffffff;
                background-color: #252526;
                border: 2px solid #000000;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                font-family: Segoe UI;
            }
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-family: Segoe UI;
                margin-top: 20px;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 18px;
                margin-top: 20px;
                font-family: Segoe UI;
            }
            QComboBox {
                color: #ffffff;
                background-color: #252526;
                border: 2px solid #000000;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                font-family: Segoe UI;
            }
            QComboBox QAbstractItemView {
                font-family: Segoe UI;
                color: #ffffff;
                background-color: #252526;
            }
        """)

        self.pdf_label = QLabel("Select PDF file:")
        self.pdf_entry = QLineEdit()
        self.pdf_button = QPushButton("")
        self.pdf_button.setIcon(QIcon('res/browse.png'))
        self.pdf_button.setFixedSize(QSize(45, 45))
        self.pdf_button.clicked.connect(self.select_pdf_file)

        self.script_label = QLabel("Select script file:")
        self.script_entry = QLineEdit()
        self.script_button = QPushButton("")
        self.script_button.setIcon(QIcon('res/browse.png'))
        self.script_button.setFixedSize(QSize(45, 45))
        self.script_button.clicked.connect(self.select_script_file)

        self.pptx_label = QLabel("Select pptx file:")
        self.pptx_entry = QLineEdit()
        self.pptx_button = QPushButton("")
        self.pptx_button.setIcon(QIcon('res/browse.png'))
        self.pptx_button.setFixedSize(QSize(45, 45))
        self.pptx_button.clicked.connect(self.select_pptx_file)

        self.subtitles_checkbox = QCheckBox("Enable Subtitles")

        self.voice_label = QLabel("Choose TTS Voice:")
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

        self.video_name_label = QLabel("Video Name:")
        self.video_name_entry = QLineEdit()

        self.video_location_label = QLabel("Video Location:")
        self.video_location_entry = QLineEdit()
        self.video_location_button = QPushButton("")
        self.video_location_button.setIcon(QIcon('res/browse.png'))
        self.video_location_button.setFixedSize(QSize(45, 45))
        self.video_location_button.clicked.connect(self.select_video_location)

        self.generate_button = QPushButton("Generate Video")
        self.generate_button.clicked.connect(self.generate_video)

        self.generate_demo_button = QPushButton("Generate Demo")
        self.generate_demo_button.clicked.connect(self.generate_demo_video)

        self.loading_spinner = pyqtspinner.WaitingSpinner(self, True, True)

        self.btn_layout = QHBoxLayout()

        self.btn_layout.addWidget(self.generate_button)
        self.btn_layout.addWidget(self.generate_demo_button)

        self.script_pptx_labels_layout = QHBoxLayout()
        self.script_pptx_labels_layout.addWidget(self.script_label)
        self.script_pptx_labels_layout.addWidget(self.pptx_label)

        self.script_pptx_layout = QHBoxLayout()
        self.script_pptx_layout.addWidget(self.script_entry)
        self.script_pptx_layout.addWidget(self.script_button)
        self.script_pptx_layout.addWidget(self.pptx_entry)
        self.script_pptx_layout.addWidget(self.pptx_button)

        self.pdf_layout = QHBoxLayout()
        self.pdf_layout.addWidget(self.pdf_entry)
        self.pdf_layout.addWidget(self.pdf_button)

        self.video_location_layout = QHBoxLayout()
        self.video_location_layout.addWidget(self.video_location_entry)
        self.video_location_layout.addWidget(self.video_location_button)

        layout = QVBoxLayout()
        layout.addLayout(self.script_pptx_labels_layout)
        layout.addLayout(self.script_pptx_layout)
        layout.addWidget(self.pdf_label)
        layout.addLayout(self.pdf_layout)
        layout.addWidget(self.subtitles_checkbox)
        layout.addWidget(self.loading_spinner)
        layout.addWidget(self.voice_label)
        layout.addWidget(self.voice_combo)
        layout.addWidget(self.video_name_label)
        layout.addWidget(self.video_name_entry)
        layout.addWidget(self.video_location_label)
        layout.addLayout(self.video_location_layout)
        layout.addLayout(self.btn_layout)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.video_thread = None

    def select_pdf_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF file", "", "PDF files (*.pdf)")
        self.pdf_entry.setText(file_path)

    def select_script_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select script file", "", "Text files (*.txt)")
        self.script_entry.setText(file_path)

    def select_pptx_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PowerPoint file",
                                                   "", "PowerPoint files (*.pptx *.ppt)")
        self.pptx_entry.setText(file_path)

    def select_video_location(self):
        default_location = os.path.dirname(os.path.realpath(__file__))
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory", default_location)
        self.video_location_entry.setText(dir_path)

    def generate_video(self):
        pdf_file = self.pdf_entry.text()
        script_file = self.script_entry.text()
        subtitles_enabled = self.subtitles_checkbox.isChecked()
        selected_voice = self.voice_combo.currentText()
        video_name = self.video_name_entry.text()
        video_location = self.video_location_entry.text()

        if pdf_file and script_file and video_name and video_location:
            self.loading_spinner.start()
            self.generate_button.setEnabled(False)

            # Start video generation thread
            self.video_thread = VideoGenerationThread(pdf_file, script_file, subtitles_enabled, selected_voice,
                                                      video_name, video_location)
            self.video_thread.video_generated.connect(self.video_generation_complete)
            self.video_thread.start()

    def generate_demo_video(self):
        pdf_file = self.pdf_entry.text()
        script_file = self.script_entry.text()
        pptx_file = self.pptx_entry.text()
        video_name = self.video_name_entry.text()
        video_location = self.video_location_entry.text()
        if pdf_file and (script_file or pptx_file) and video_name and video_location:
            self.loading_spinner.start()
            self.generate_button.setEnabled(False)

            # Start video generation thread
            self.video_thread = DemoGenerationThread(pdf_file, script_file, pptx_file, video_name, video_location)
            self.video_thread.video_generated.connect(self.video_generation_complete)
            self.video_thread.start()

    def video_generation_complete(self):
        self.loading_spinner.stop()
        self.generate_button.setEnabled(True)

        ### Delete all temp files ###
        # Get the parent directory path
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # Path to the folder to clear
        folder_to_clear = os.path.join(parent_dir, "dir")

        # Iterate over all files and directories in the folder
        for file_or_dir in os.listdir(folder_to_clear):
            # Construct the full path to the file or directory
            file_or_dir_path = os.path.join(folder_to_clear, file_or_dir)

            # Check if it's a file
            if os.path.isfile(file_or_dir_path):
                # Remove the file
                os.remove(file_or_dir_path)
            # Check if it's a directory
            elif os.path.isdir(file_or_dir_path):
                # Remove the directory and its contents recursively
                os.rmdir(file_or_dir_path)

        # Create a message box
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(
            f"Generation complete. Video is located at {self.video_location_entry.text()}/{self.video_name_entry.text()}")
        msg_box.setWindowTitle("Video Generated")
        msg_box.setStandardButtons(QMessageBox.Ok)

        # Show the message box
        msg_box.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoGenerationWindow()
    window.show()
    sys.exit(app.exec_())
