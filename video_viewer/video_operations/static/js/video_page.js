const dropArea = document.getElementById("drop-area")
const inputFile = document.getElementById("upload-video")
const videoView = document.getElementById("video-view")
const videoPreview = document.getElementById('videoPreview');

const uploadButton = document.getElementById("upload-button")
const deleteVideoButton = document.getElementById("delete-video-button")

const flipCheck = document.getElementById("flip_operation")
const rotationSpan = document.getElementById("rotation-span")
const volumeSpan = document.getElementById("volume-span")
const extensionSelect = document.getElementById("extension-select")
const resolutionSelect = document.getElementById("resolution-select")
const muteCheck = document.getElementById("mute_operation")
const backgroundRemoveCheck = document.getElementById("background_remove")
const faceBlurCheck = document.getElementById("face_blur")

const startMinuteInput = document.getElementById("start-minute-input")
const startSecondInput = document.getElementById("start-second-input")

const endMinuteInput = document.getElementById("end-minute-input")
const endSecondInput = document.getElementById("end-second-input")

import BACKEND_URL from './config.js';


inputFile.addEventListener("change", uploadVideo);

dropArea.addEventListener("dragover", function(e){
    e.preventDefault();
})
dropArea.addEventListener("drop", function(e){
    e.preventDefault();
    inputFile.files = e.dataTransfer.files;
    uploadVideo();
})


function uploadVideo(){
    const file = inputFile.files[0]; // Get the first selected file
    if (file) {
        // Create a URL for the uploaded video
        const videoURL = URL.createObjectURL(file);

        videoPreview.src = videoURL;
        videoPreview.style.display = 'block';
        deleteVideoButton.style.display = 'block';

        dropArea.style.display = "none";
    }

}

deleteVideoButton.addEventListener('click', () =>{
    inputFile.value = '';
    videoPreview.src = '';
    videoPreview.load();

    videoPreview.style.display = 'none';
    deleteVideoButton.style.display = 'none';

    dropArea.style.display = "block";
})

uploadButton.addEventListener('click', async () =>{
    const file = inputFile.files[0]; // Get the selected file

    if (!file) {
        
        return;
    }

    // Collect selected operations
    const operations = {};
    
    operations.flip = flipCheck.checked
    operations.rotation = rotationSpan.textContent
    operations.volume = volumeSpan.textContent
    operations.extension = extensionSelect.value
    operations.resolution = resolutionSelect.value
    operations.mute = muteCheck.checked
    operations.background_remove = backgroundRemoveCheck.checked
    operations.face_blur = faceBlurCheck.checked

    console.log(startMinuteInput.value)
    operations.start = Number(startMinuteInput.value) * 60 + Number(startSecondInput.value)
    operations.end = Number(endMinuteInput.value) * 60 + Number(endSecondInput.value)
    console.log(operations)

    // Prepare FormData
    const formData = new FormData();
    formData.append('video', file);
    formData.append('operations', JSON.stringify(operations));
    let progressInterval = setInterval(updateProgress, 1000);
    
    try {
        const response = await fetch(`${BACKEND_URL}/upload/`, {
            method: 'POST',
            body: formData
        });
        
        


        if (response.ok) {
            const contentType = response.headers.get('Content-Type');
            const blob = await response.blob();
            const blobURL = URL.createObjectURL(blob);

            
            console.log("Processing complete. Stopped updating progress.");

            if (contentType === 'image/gif') {
                const gifPreview = document.getElementById('gifPreview');
                gifPreview.src = blobURL;
                gifPreview.style.display = 'block';

                const videoPreview = document.getElementById('videoPreview');
                videoPreview.style.display = 'none';
                deleteVideoButton.style.display = 'block';
            } else if (['video/mp4', 'video/avi', 'video/quicktime'].includes(contentType)) {
                const videoPreview = document.getElementById('videoPreview');
                videoPreview.src = blobURL;
                videoPreview.style.display = 'block';

                const gifPreview = document.getElementById('gifPreview');
                gifPreview.style.display = 'none';
                deleteVideoButton.style.display = 'block';
            }else if(['audio/mpeg'].includes(contentType)){
                const link = document.createElement("a");
                const audioUrl = blobURL
                link.href = audioUrl; // URL of the MP3 file from the server
                link.download = ""; // Optional: Specify a default filename
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link); // Clean up the temporary link
            }
        } 
    } catch (error) {
        clearInterval(progressInterval); 
        console.error("Error:", error);
    }
    clearInterval(progressInterval); 
})


const volumeUpButton = document.getElementById("volume-up")
const volumeDownButton = document.getElementById("volume-down")

const rotateRightButton = document.getElementById("rotate-right")
const rotateLeftButton = document.getElementById("rotate-left")

volumeUpButton.onclick  = function(){
    if(volumeSpan.textContent=="1"){
        volumeSpan.textContent=2
        return
    }
    if(volumeSpan.textContent==2){
        volumeSpan.textContent=4
        return
    }
    if(volumeSpan.textContent==4){
        volumeSpan.textContent=8
        return
    }
    if(volumeSpan.textContent==-8){
        volumeSpan.textContent=-4
        return
    }
    if(volumeSpan.textContent==-4){
        volumeSpan.textContent=-2
        return
    }
    if(volumeSpan.textContent==-2){
        volumeSpan.textContent=1
        return
    }
}
volumeDownButton.onclick  = function(){
    if(volumeSpan.textContent==1){
        volumeSpan.textContent=-2
        return
    }
    if(volumeSpan.textContent==-2){
        volumeSpan.textContent=-4
        return
    }
    if(volumeSpan.textContent==-4){
        volumeSpan.textContent=-8
        return
    }
    if(volumeSpan.textContent==8){
        volumeSpan.textContent=4
        return
    }
    if(volumeSpan.textContent==4){
        volumeSpan.textContent=2
        return
    }
    if(volumeSpan.textContent==2){
        volumeSpan.textContent=1
        return
    }
}

rotateLeftButton.onclick = function(){
    if(rotationSpan.textContent>-315){
        rotationSpan.textContent = Number(rotationSpan.textContent)-45
    }
}

rotateRightButton.onclick = function(){
    if(rotationSpan.textContent<315){
        rotationSpan.textContent = Number(rotationSpan.textContent)+45
    }
}





function updateProgress() {
    fetch(`${BACKEND_URL}/progress/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("progress").innerText = data.progress;

            // Check if the video processing is done, and stop the updates if it is
            if (data.progress.includes("100%")) {
                clearInterval(progressInterval);  // Stop the progress updates
                console.log("Processing complete. Stopped updating progress.");
            }
        });
}