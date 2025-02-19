import json
import os
import tempfile

import numpy as np
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from moviepy.editor import VideoFileClip, vfx
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import Profile
from colorama import Fore

from PIL import Image
import cv2

from .video_processing.utils import remove_background_function, blur_faces


@login_required
def update_profile_image(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get("action")
            profile = request.user.profile

            # Logic to update image_id
            if action == "next":
                profile.image_id = 0 if profile.image_id >=2 else profile.image_id + 1
            elif action == "prev":
                profile.image_id = 2 if profile.image_id <= 0 else profile.image_id - 1

            profile.save()

            # Return a JSON response with the updated image URL
            image_mapping = {
                0: '/static/images/trex.png',
                1: '/static/images/triceratops.png',
                2: '/static/images/stegozaur.png',
            }
            return JsonResponse({"success": True, "image_url": image_mapping[profile.image_id]})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    # Handle invalid request methods
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile  # Assuming you have a Profile model
    context = {
        'user': user,
        'profile_image': profile.image_id,  # Pass the image_id to the template
    }
    return render(request, 'profile_page.html', context)

def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        print(f"{email=}")
        print(f"{password1=}")
        print(f"{password2=}")
        # Add user to database
        # Check if passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return render(request, 'register.html')

        username = email.split('@')[0]
        # Check if the username (login) already exists
        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists() :
            messages.error(request, "Login already exists!")
        else:
            # Create the user
            print(f"{Fore.CYAN} Create User {Fore.RESET}")
            user = User.objects.create_user(username=username, password=password1, email=email)
            Profile.objects.create(user=user, image_id=0)
            messages.success(request, "Account created successfully!")
            return redirect('../login')  # Redirect to the login page

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(email)
        print(password)
        # Find the username associated with the provided email
        try:
            username = User.objects.get(email=email).username
            print(username)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password!")
            return render(request, 'login.html')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        print(user)
        if user is not None:
            # Log the user in
            print("login")
            login(request, user)
            return redirect('/')  # Redirect to the main page (replace 'main' with your route name)
        else:
            messages.error(request, "Invalid email or password!")

    return render(request, 'login.html')

def main(request):
    print(f"User authenticated: {request.user.is_authenticated}")
    print(request.user.username)


    context = {
        'user': request.user,
        'profile_image': request.user.profile.image_id if request.user.is_authenticated else None
    }
    template = loader.get_template('video_page.html')
    return HttpResponse(template.render(context, request))

def logout_view(request):
    logout(request)  # Log the user out
    return redirect('/')

@csrf_exempt
def upload(request):
    if request.method == 'POST':
        # Get the uploaded video
        video_file = request.FILES.get('video')

        # Get the operations JSON and decode it
        operations = request.POST.get('operations')
        if operations:
            operations = json.loads(operations)

        print(f"Received video file: {video_file}")
        print(f"Operations: {operations}")

        try:
            # Check if the file is already stored on disk
            if hasattr(video_file, 'temporary_file_path'):
                video_path = video_file.temporary_file_path()
            else:
                # File is in memory; write it to a temporary location
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                    temp_file.write(video_file.read())
                    video_path = temp_file.name

            # Load the video using MoviePy
            with VideoFileClip(video_path) as clip:
                print(f"{Fore.LIGHTBLUE_EX} {clip.duration=} {Fore.RESET}")
                if not (float(operations.get("start",0)) == 0) or not (float(operations.get("end",0)) == 0):
                    start_time = float(operations.get("start"))
                    end_time = float(operations.get("end"))
                    if end_time < clip.duration and end_time > start_time:
                        print(f"clip.duration = {clip.duration} start:{start_time} end:{end_time}")
                        clip = clip.subclip(start_time, end_time)

                if (volume_change := operations.get("volume")) != "1" and not operations.get("mute"):
                    if int(volume_change)<0:
                        clip = clip.volumex(1/int(volume_change))
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

                resolution = operations.get("resolution")
                if resolution is not None and not (resolution == "None"):
                    # Parse the resolution string into a tuple of integers
                    width, height = map(int, resolution.strip("()").split(","))

                    # Resize the video to the specified resolution
                    clip = clip.resize(newsize=(width, height))

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

                    with tempfile.NamedTemporaryFile(suffix=f".{suffix}", delete=False) as temp_output_file:
                        temp_output_path = temp_output_file.name
                        clip.write_videofile(temp_output_path, codec="libx264", audio_codec="aac")

                    # Return the video
                    with open(temp_output_path, "rb") as output_file:
                        response = HttpResponse(output_file.read(), content_type=f"video/{content_type}")
                        response["Content-Disposition"] = f'inline; filename="processed_video.{suffix}"'
                        return response



        except Exception as e:
            print(f"Error processing video: {e}")
            return HttpResponse("Error processing video.", status=500)

    return HttpResponse("Invalid request", status=400)


def stitcher(request):
    return render(request, 'stitcher.html')
@csrf_exempt
def stitch_images(request):
    if request.method == "POST":
        # Ensure files are uploaded
        if 'images' not in request.FILES:
            return JsonResponse({"error": "No images uploaded"}, status=400)

        images_list = []

        print(os.getcwd())

        for file in request.FILES.getlist('images'):
            # Read file into OpenCV format
            image = Image.open(file)  # Read with PIL
            image = np.array(image)  # Convert to NumPy array
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # Convert to OpenCV BGR format

            images_list.append(image)

        if len(images_list) < 2:
            return JsonResponse({"error": "At least two images are required for stitching"}, status=400)



        stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)

        status, panorama = stitcher.stitch(images_list)
        # Create a Stitcher object and stitch the images
        # stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
        # status, stitched = stitcher.stitch(images_list)
        #
        # if status != cv2.Stitcher_OK:
        #     print("Error during stitching: Status Code", status)
        #     return None
        #
        # # Add a border around the stitched image
        # stitched = cv2.copyMakeBorder(stitched, 10, 10, 10, 10, cv2.BORDER_CONSTANT, (0, 0, 0))
        #
        # # Convert to grayscale and threshold
        # gray = cv2.cvtColor(stitched, cv2.COLOR_BGR2GRAY)
        # thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)[1]
        # cv2.imwrite(f"{os.getcwd()}thresh.png", thresh)
        # # Find the external contours
        # cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # cnts = imutils.grab_contours(cnts)
        # c = max(cnts, key=cv2.contourArea)
        #
        # # Create a mask with a bounding rectangle
        # mask = np.zeros(thresh.shape, dtype="uint8")
        # (x, y, w, h) = cv2.boundingRect(c)
        # cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        #
        # # Erode the mask to find the largest inner rectangle
        # minRect = mask.copy()
        # sub = mask.copy()
        # while cv2.countNonZero(sub) > 0:
        #     minRect = cv2.erode(minRect, None)
        #     sub = cv2.subtract(minRect, thresh)
        #
        # # Find contours of the minimum rectangular mask
        # cnts = cv2.findContours(minRect.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # cnts = imutils.grab_contours(cnts)
        # c = max(cnts, key=cv2.contourArea)
        # (x, y, w, h) = cv2.boundingRect(c)
        #
        # # Crop the final stitched image
        # panorama = stitched[y:y + h, x:x + w]

        if panorama is None:
            return JsonResponse({"error": "Stitching failed"}, status=500)

        cv2.imwrite(f"{os.getcwd()}panorama.png", panorama)

        # Convert stitched image to bytes (for response)
        _, buffer = cv2.imencode('.png', panorama)
        return HttpResponse(buffer.tobytes(), content_type="image/png")

    return JsonResponse({"error": "Invalid request method"}, status=405)