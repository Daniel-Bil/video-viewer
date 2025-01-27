import json
import tempfile

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



                if (rotation_change := operations.get("rotation")) != '0':
                    clip = clip.rotate(int(rotation_change))

                if operations.get("mute"):
                    clip = clip.without_audio()

                resolution = operations.get("resolution")
                if resolution:
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
