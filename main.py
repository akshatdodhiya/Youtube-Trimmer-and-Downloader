from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5 import uic
import os
import time
import subprocess
import json


class YtGui(QMainWindow):
    def __init__(self):
        # noinspection PyArgumentList
        super(YtGui, self).__init__()
        uic.loadUi("UI/design.ui", self)  # Loads ui file from UI directory, made using Qt designer
        self.setWindowIcon(QIcon("UI/icon.png"))
        akshat = QPixmap("UI/watermark.png")  # Load watermark image
        self.watermark.setPixmap(akshat)  # Show watermark image instead of normal label
        # Visit website label with hyperlink
        self.website.setText("<a href=https://akshatdodhiya.blogspot.com>Visit my website! 🌐</a>")
        # Buy me a coffee label with hyperlink
        self.bmc.setText("<a href=https://www.buymeacoffee.com/akshatdodhiya>Buy Me A Coffee ☕</a>")

        self.setFixedSize(self.width(), self.height())  # Fixed window size and disable maximize & minimize button
        self.show()  # Show Window

        # Connect buttons to their respective functions
        self.ok_btn.clicked.connect(self.get_video_details)
        self.selectPath_btn.clicked.connect(self.get_path)
        self.download_btn.clicked.connect(self.download_video)
        self.trimVideo_btn.clicked.connect(self.trim_video)
        self.changePath_btn.clicked.connect(lambda: self.get_path(no_tag=True))

    # noinspection PyTypeChecker
    def get_video_details(self):
        """
        Check the validation of input link and then displays the youtube video details (if found)
        :return: None
        """
        from pytube import YouTube
        import pytube.exceptions
        try:
            # Initialize pytube module
            # on_progress_callback --> Connected to progress_function which is connected to progress_bar
            # of the ui which displays the download progress
            # on_complete_callback --> Connected to download_complete function which displays a message
            # after completing of download
            self.yt = YouTube(self.link_input.text(), on_progress_callback=self.progress_function,
                              on_complete_callback=lambda x, y: self.download_complete())
        except pytube.exceptions.RegexMatchError:
            self.show_error("Invalid Link! Please enter a valid youtube link")
        except pytube.exceptions.VideoPrivate:
            self.show_error("Private Video! Please try another video")
        except:
            self.show_error("Error Occurred! Please Retry")
        else:

            # List to store video Details
            self.videoDetails = [("Title:                  " + self.yt.title),
                                 ("Author:             " + self.yt.author),
                                 ("Video Length:  " + str(int(self.yt.length / 60)) +
                                  " Minutes and " + str(self.yt.length % 60) + " Seconds")]

            # Want to trim check box is checked or not
            self.trim = self.trim_checkBox.isChecked()

            # Disable some elements
            self.link_label.setEnabled(False)
            self.link_input.setEnabled(False)
            self.trim_checkBox.setEnabled(False)
            self.ok_btn.setEnabled(False)

            # Enable some of the elements
            self.videoDetails_label.setEnabled(True)
            self.videoDetails_list.setEnabled(True)
            self.videoQuality_label.setEnabled(True)
            self.videoQuality_list.setEnabled(True)
            self.tag_label.setEnabled(True)
            self.tag_input.setEnabled(True)
            self.path_label.setEnabled(True)
            self.defaultPath_checkBox.setEnabled(True)

            # Get default path to store the videos
            try:
                with open("config.json", "r") as config:
                    config = json.load(config)
                    self.path = dict(config).get("PATH")
                    if self.path == "":
                        raise Exception
                    self.default_path = True  # Default path found
                    self.selectPath_btn.setText("Select Tag")  # Change the text of button from Select path
                    self.path_label.setText(
                        "Path: " + self.path + "/" + self.yt.title)  # Change label text to Path found
                    self.changePath_btn.setEnabled(True)  # Enable change path button

            except FileNotFoundError:
                self.default_path = False  # No default path found
            except:
                # Deletes the file if empty
                if os.path.exists("config.json"):
                    os.remove("config.json")
                self.default_path = False  # No default path found

            self.selectPath_btn.setEnabled(True)  # Enable Select path/Select tag button
            self.videoDetails_list.addItems(self.videoDetails)  # Show details of the youtube video

            self.display_quality()  # Call method to display video quality

    def show_error(self, message):
        """
        Function that displays a message window for errors
        :param message: A message to be displayed as an error message
        :return: None
        """
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setWindowTitle("Error!")
        error_msg.setText(message)
        error_msg.exec()

    def progress_function(self, stream, chunk, bytes_remaining):
        """
        Function to display the progress of video i.e being downloaded
        :param stream: No use
        :param chunk: No use
        :param bytes_remaining: Used for calculating bytes remaining, to show progress
        :return: None
        """
        self.download_progressBar.setValue(int(round((1 - bytes_remaining / self.video.filesize) * 100, 3)))

    def download_complete(self):
        """
        Function that displays message after video downloads successfully
        :return: None
        """
        message = QMessageBox()
        message.setIcon(QMessageBox.Question)
        message.setStandardButtons(QMessageBox.Ok | QMessageBox.Open)
        message.setDefaultButton(QMessageBox.Ok)
        message.setWindowTitle("Success!")
        message.setText("Video downloaded!")
        message.buttonClicked.connect(self.after_download)
        message.exec()

    def after_download(self, btn):
        """
        Function connected to download_complete() and used to do specific task depending on user's click
        :param btn: Name of the button pressed
        :return:
        """
        if btn.text() == "Open":  # If open button clicked
            file_path = self.path.replace("/", "\\") + "\\" + self.video_name  # Full path where video is downloaded
            subprocess.Popen(f'explorer /select,{file_path}')  # Open the path with video selected
        elif btn.text() == "OK" and not self.trim:  # If OK button is clicked and trim is not selected
            self.close()  # Close the app

    def display_quality(self):
        """
        Display the available qualities to for downloading the video
        :return: None
        """
        stream = str(self.yt.streams.filter(progressive=True))  # Filter streams with both Video & Audio
        stream_list = stream.split(", ")
        self.tags = []

        # Logic that filters the important data from streams
        for i in range(0, len(stream_list)):
            st = stream_list[i].split(" ")
            qualities = ["Tag number :     " + st[1].replace('itag="', '').replace('"', '') +
                         "   |   " +
                         "Quality: " + st[3].replace('res="', '').replace('"', '')]
            # Append tags to check for valid input of tags by the user
            self.tags.append(st[1].replace('itag="', '').replace('"', ''))
            self.videoQuality_list.addItems(qualities)  # Show available qualities to the user

    def get_path(self, no_tag=False):
        """
        Function that asks user to select path for video to be saved
        :param no_tag: Used for change path button, if true then it doesn't check for valid tag
        :return: None
        """
        self.tag_number = self.tag_input.text()  # Get input of the tag number entered by the user

        if self.tag_number == "":
            self.show_error("Please enter a tag number!")
        elif self.tag_number not in self.tags:
            self.show_error("Invalid Tag Number!")
        else:
            if not self.default_path:  # Ask user to select path if no default path found
                self.path = QFileDialog.getExistingDirectory(self, caption="Select Path to Store video")
                self.path_label.setText("Path: " + self.path + "/" + self.yt.streams.
                                        get_by_itag(self.tag_number).default_filename)
            elif self.default_path and no_tag:  # Ask user to change the path
                self.path = QFileDialog.getExistingDirectory(self, caption="Select New Path to Store video")
                self.path_label.setText("Path: " + self.path + "/" + self.yt.streams.
                                        get_by_itag(self.tag_number).default_filename)

            self.download_btn.setEnabled(True)  # Enable the download button if all condition are valid

    def download_video(self):
        """
        Check for default path and saves the config and then downloads the video
        :return: None
        """
        self.download_progressBar.setEnabled(True)  # Enable the progress bar to display progress
        if self.defaultPath_checkBox.isChecked():
            with open("config.json", "w") as config:
                json.dump(dict({"PATH": self.path}), config)  # Store the default path config
        self.video = self.yt.streams.get_by_itag(self.tag_number)  # Get the video by i_tag
        # Get the default name of the video
        self.video_name = self.yt.streams.get_by_itag(self.tag_number).default_filename
        self.video.download(self.path)  # Download the video

        if self.trim:  # If want to trim checkBox is ticked
            # Enable required labels, buttons and text fields
            self.trim_label.setEnabled(True)
            self.startTime_label.setEnabled(True)
            self.startTime_input.setEnabled(True)
            self.endTime_label.setEnabled(True)
            self.endTime_input.setEnabled(True)
            self.trimVideo_btn.setEnabled(True)

    def trim_video(self):
        """
        Trims the video and remove the original redundant video and keeps the trimmed one
        :return: None
        """
        import moviepy.editor as editor

        # Splits the input time in minutes and seconds, then maps it to int function to convert both
        # the elements of the list into integer for comparison and calculation purposes
        start_time = list(map(int, self.startTime_input.text().split(":")))
        end_time = list(map(int, self.endTime_input.text().split(":")))

        # Error if seconds more than 60
        if start_time[1] > 60:
            self.show_error("Invalid Start Time!")
        elif end_time[1] > 60:
            self.show_error("Invalid End Time!")
        else:
            # Convert minutes and seconds into seconds
            start_secs = start_time[0] * 60 + start_time[1]
            end_secs = end_time[0] * 60 + end_time[1]

            # Error if endTime is less than startTime
            if end_secs - start_secs <= 0:
                self.show_error("Start Time cannot be greater or equal to End Time")
            else:
                # Loads the video file downloaded
                clip = editor.VideoFileClip(self.path + "\\" + self.video_name)
                if end_secs > clip.duration:
                    # Error if end_secs is more than total length of the video
                    self.show_error("Invalid End Time!")
                elif start_secs > clip.duration:
                    # Error if start_secs is more than total length of the video
                    self.show_error("Invalid Start Time")
                else:
                    # Get the clip between start and end seconds specified by the user
                    clip = clip.subclip(start_secs, end_secs)
                    ext = self.video_name.split(".")[1]  # Extension of the file to select codec
                    # Available codecs to convert
                    codecs_available = {"libx264": "mp4", "png": "avi", "libvorbis": "ogv", "libvpx": "webm"}

                    def get_key(val):
                        """
                        Function that returns key for specified value
                        :param val: Value whose key has to be found
                        :return: key
                        """
                        for key, value in codecs_available.items():
                            if val == value:
                                return key
                        return None

                    # Full path where the file after trimming will be stored
                    file_path = f'{self.path}\\{self.video_name.split(".")[0]} - Youtube Trimmer by Akshat Dodhiya.' \
                                f'{self.video_name.split(".")[1]}'

                    # Check if the codec is available for current file extension
                    codec = get_key(ext)

                    if codec is None:  # Error if codec not available for the current video file extension
                        self.show_error("This video cannot be trimmed please choose another one!")
                    else:
                        try:
                            # Disable trimVideo button
                            self.trimVideo_btn.setEnabled(False)
                            # Save the video file on specified path with appropriate codec
                            if os.path.exists(file_path):
                                file_path = f'{self.path}\\{self.video_name.split(".")[0]}' \
                                            f' - Youtube Trimmer by Akshat Dodhiya - {int(time.time())}.' \
                                            f'{self.video_name.split(".")[1]}'
                                clip.write_videofile(file_path, codec=codec)
                            else:
                                raise Exception
                            editor.VideoFileClip.close(clip)  # Close clip if tasked accomplished
                            # Delete original big video file after successful trimming
                            if os.path.exists(self.path + "\\" + self.video_name):
                                os.remove(self.path + "\\" + self.video_name)

                        except:
                            self.show_error("Unknown Error occurred while trimming the video! Please try again.")
                        else:  # Display success message if trimming completed successfully
                            message = QMessageBox()
                            message.setIcon(QMessageBox.NoIcon)
                            message.setWindowTitle("Success!")
                            message.setText("Video Trimmed Successfully!")
                            message.exec()
                            file_path = file_path.replace("/", "\\")
                            subprocess.Popen(f'explorer /select,{file_path}')  # Open the path with video selected
                            self.close()


if __name__ == "__main__":
    app = QApplication([])  # Initializing the application
    YtGui()  # Setting the window
    app.exec()  # Executing the app
