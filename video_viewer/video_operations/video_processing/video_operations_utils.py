import multiprocessing
import os
from pathlib import Path

from colorama import Fore
from django.http import HttpResponse
from moviepy.editor import VideoFileClip, vfx
from proglog import ProgressBarLogger

import tempfile

from moviepy.video.compositing.concatenate import concatenate_videoclips

from .utils import blur_faces, remove_background_function


class MyBarLogger(ProgressBarLogger):

    def callback(self, **changes):
        # Every time the logger message is updated, this function is called with
        # the `changes` dictionary of the form `parameter: new value`.
        for parameter, value in changes.items():
            print(f'Parameter {parameter} is now {value}')

    def bars_callback(self, bar, attr, value, old_value=None):
        # Every time the logger progress is updated, this function is called
        percentage = (value / self.bars[bar]['total']) * 100
        print(f"{bar}: {attr} {percentage:.2f}%")

        # Save the progress to the "progress.txt" file
        with open("progress.txt", "w") as f:
            f.write(f"Processed {value}/{self.bars[bar]['total']} seconds\n")
            f.write(f"Progress: {percentage:.2f}%\n")



def process_video(video_path: Path, operations: dict) -> HttpResponse:
    print("Process video")
    # Load the video using MoviePy
    with VideoFileClip(video_path) as clip:
        print(f"{Fore.LIGHTBLUE_EX} {clip.duration=} {Fore.RESET}")

        if not (float(operations.get("start", 0)) == 0) or not (float(operations.get("end", 0)) == 0):
            start_time = float(operations.get("start"))
            end_time = float(operations.get("end"))
            if end_time < clip.duration and end_time > start_time:
                print(f"clip.duration = {clip.duration} start:{start_time} end:{end_time}")
                clip = clip.subclip(start_time, end_time)


        resolution = operations.get("resolution")
        if resolution is not None and not (resolution == "None"):
            # Parse the resolution string into a tuple of integers
            width, height = map(int, resolution.strip("()").split(","))

            # Resize the video to the specified resolution
            clip = clip.resize(newsize=(width, height))

        if (volume_change := operations.get("volume")) != "1" and not operations.get("mute"):
            if int(volume_change) < 0:
                clip = clip.volumex(1 / int(volume_change))
            else:
                clip = clip.volumex(int(volume_change))

        # Check if the operation is to extract audio
        if operations.get("extension") == "MP3":
            # Use a temporary file to save the audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_output_file:
                temp_audio_path = temp_output_file.name

            # Write the audio to the temporary file
            clip.audio.write_audiofile(temp_audio_path)

            # Open the file again to send it in the response
            with open(temp_audio_path, "rb") as audio_file:
                response = HttpResponse(audio_file.read(), content_type="audio/mpeg")
                response["Content-Disposition"] = 'attachment; filename="output_audio.mp3"'

            return response

        if operations.get("flip"):
            clip = clip.fx(vfx.mirror_x)

        if operations.get("face_blur"):
            print("face_blur True")
            clip = clip.fl_image(blur_faces)

        if operations.get("background_remove"):
            print("background remove True")
            clip = clip.fl_image(remove_background_function)

        if (rotation_change := operations.get("rotation")) != '0':
            clip = clip.rotate(int(rotation_change))

        if operations.get("mute"):
            clip = clip.without_audio()

        if operations.get("extension") == "GIF":
            # Save the processed video as a GIF
            with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as temp_output_file:
                temp_output_path = temp_output_file.name
                clip.write_gif(temp_output_path, fps=1)  # Adjust fps as needed

            # Return the GIF
            with open(temp_output_path, "rb") as output_file:
                response = HttpResponse(output_file.read(), content_type="image/gif")
                response["Content-Disposition"] = 'inline; filename="processed.gif"'
                print(response)
                return response
        else:
            # Save the processed video as MP4 (default case)
            if operations.get("extension") == "MP4":
                suffix = "mp4"
                content_type = "mp4"
            elif operations.get("extension") == "AVI":
                suffix = "avi"
                content_type = "x-msvideo"
            elif operations.get("extension") == "MOV":
                suffix = "mov"
                content_type = "quicktime"
            else:
                raise ValueError("Unsupported extension")

            logger = MyBarLogger()

            with tempfile.NamedTemporaryFile(suffix=f".{suffix}", delete=False) as temp_output_file:
                temp_output_path = temp_output_file.name
                clip.write_videofile(temp_output_path, codec="libx264", audio_codec="aac", logger=logger)


            # Return the video
            with open(temp_output_path, "rb") as output_file:
                response = HttpResponse(output_file.read(), content_type=f"video/{content_type}")
                response["Content-Disposition"] = f'inline; filename="processed_video.{suffix}"'
                return response













# def processing_function(clip, operations):
#     resolution = operations.get("resolution")
#     if resolution is not None and not (resolution == "None"):
#         # Parse the resolution string into a tuple of integers
#         width, height = map(int, resolution.strip("()").split(","))
#
#         # Resize the video to the specified resolution
#         clip = clip.resize(newsize=(width, height))
#
#     if (volume_change := operations.get("volume")) != "1" and not operations.get("mute"):
#         if int(volume_change) < 0:
#             clip = clip.volumex(1 / int(volume_change))
#         else:
#             clip = clip.volumex(int(volume_change))
#
#     if operations.get("flip"):
#         clip = clip.fx(vfx.mirror_x)
#
#     if operations.get("face_blur"):
#         clip = clip.fl_image(blur_faces)
#
#     if operations.get("background_remove"):
#         clip = clip.fl_image(remove_background_function)
#
#     if (rotation_change := operations.get("rotation")) != '0':
#         clip = clip.rotate(int(rotation_change))
#
#     if operations.get("mute"):
#         clip = clip.without_audio()
#
#     return clip
#
# def process_video_multicore(video_path: Path, operations: dict) -> HttpResponse:
#     print("process_video_multicore")
#     output_dir = "media"
#
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#
#     number_of_cores = 4 if multiprocessing.cpu_count() >= 4 else multiprocessing.cpu_count()
#
#     print(f"{Fore.LIGHTMAGENTA_EX} NUMBER OF CORES (max4): {number_of_cores}{Fore.RESET}")
#
#     # Load the video using MoviePy
#     with VideoFileClip(video_path) as clip:
#         print(f"{Fore.LIGHTBLUE_EX} {clip.duration=} {Fore.RESET}")
#
#         if not (float(operations.get("start", 0)) == 0) or not (float(operations.get("end", 0)) == 0):
#             start_time = float(operations.get("start"))
#             end_time = float(operations.get("end"))
#             if end_time < clip.duration and end_time > start_time:
#                 print(f"clip.duration = {clip.duration} start:{start_time} end:{end_time}")
#                 clip = clip.subclip(start_time, end_time)
#                 print(f"{Fore.LIGHTBLUE_EX} shorten {clip.duration=} {Fore.RESET}")
#
#         chunk_length = clip.duration / number_of_cores
#
#         subclips = []
#         for i in range(number_of_cores):
#             start = i * chunk_length
#             end = start + chunk_length
#
#             subclip = clip.subclip(start, end)
#             subclip_path = os.path.join(output_dir, f"subclip_{i}.mp4")
#             subclip.write_videofile(subclip_path, codec="libx264", audio_codec="aac")  # Save subclip
#
#             subclip_paths.append(subclip_path)  # Append the path of each subclip
#
#         pool = multiprocessing.Pool(processes=number_of_cores)
#
#         processed_subclips = pool.map(processing_function, subclips)
#
#         pool.close()
#         pool.join()
#
#         final_video = concatenate_videoclips(processed_subclips)
#
#         # Check if the operation is to extract audio
#         if operations.get("extension") == "MP3":
#             # Use a temporary file to save the audio
#             with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_output_file:
#                 temp_audio_path = temp_output_file.name
#
#             # Write the audio to the temporary file
#             final_video.audio.write_audiofile(temp_audio_path)
#
#             # Open the file again to send it in the response
#             with open(temp_audio_path, "rb") as audio_file:
#                 response = HttpResponse(audio_file.read(), content_type="audio/mpeg")
#                 response["Content-Disposition"] = 'attachment; filename="output_audio.mp3"'
#
#             return response
#
#         if operations.get("extension") == "GIF":
#             # Save the processed video as a GIF
#             with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as temp_output_file:
#                 temp_output_path = temp_output_file.name
#                 final_video.write_gif(temp_output_path, fps=1)  # Adjust fps as needed
#
#             # Return the GIF
#             with open(temp_output_path, "rb") as output_file:
#                 response = HttpResponse(output_file.read(), content_type="image/gif")
#                 response["Content-Disposition"] = 'inline; filename="processed.gif"'
#                 print(response)
#                 return response
#         else:
#             # Save the processed video as MP4 (default case)
#             if operations.get("extension") == "MP4":
#                 suffix = "mp4"
#                 content_type = "mp4"
#             elif operations.get("extension") == "AVI":
#                 suffix = "avi"
#                 content_type = "x-msvideo"
#             elif operations.get("extension") == "MOV":
#                 suffix = "mov"
#                 content_type = "quicktime"
#             else:
#                 raise ValueError("Unsupported extension")
#
#             with tempfile.NamedTemporaryFile(suffix=f".{suffix}", delete=False) as temp_output_file:
#                 temp_output_path = temp_output_file.name
#                 final_video.write_videofile(temp_output_path, codec="libx264", audio_codec="aac")
#
#             # Return the video
#             with open(temp_output_path, "rb") as output_file:
#                 response = HttpResponse(output_file.read(), content_type=f"video/{content_type}")
#                 response["Content-Disposition"] = f'inline; filename="processed_video.{suffix}"'
#                 return response