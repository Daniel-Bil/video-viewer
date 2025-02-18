const uploadArea = document.getElementById("upload-area");
        const fileInput = document.getElementById("file-input");
        const imagePreview = document.getElementById("image-preview");

        // Handle Drag & Drop
        uploadArea.addEventListener("dragover", (e) => {
            e.preventDefault();
            uploadArea.classList.add("highlight");
        });

        uploadArea.addEventListener("dragleave", () => {
            uploadArea.classList.remove("highlight");
        });

        uploadArea.addEventListener("drop", (e) => {
            e.preventDefault();
            uploadArea.classList.remove("highlight");
            handleFiles(e.dataTransfer.files);
        });

        // Handle Click on Upload Area
        uploadArea.addEventListener("click", () => {
            fileInput.click();
        });

        fileInput.addEventListener("change", () => {
            handleFiles(fileInput.files);
        });

        function handleFiles(files) {
            if (imagePreview.children.length >= 5) {
                alert("You can only upload up to 5 images.");
                return;
            }
        
            [...files].forEach(file => {
                if (file.type.startsWith("image/")) {
                    if (imagePreview.children.length >= 5) return; // Prevent adding more than 5
        
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        addImage(e.target.result);
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

        function addImage(src) {
            const imageBox = document.createElement("div");
            imageBox.classList.add("image-box");

            const img = document.createElement("img");
            img.src = src;

            const deleteBtn = document.createElement("button");
            deleteBtn.classList.add("delete-btn");
            deleteBtn.innerHTML = "×";
            deleteBtn.addEventListener("click", () => {
                imageBox.remove();
            });

            imageBox.appendChild(img);
            imageBox.appendChild(deleteBtn);
            imagePreview.appendChild(imageBox);
        }



const uploadButton = document.getElementById("upload-button")

uploadButton.addEventListener('click', async () =>{
    const formData = new FormData();
    const images = document.querySelectorAll(".image-box img");
    images.forEach((img, index) => {
        const file = dataURItoBlob(img.src); // Convert base64 to file
        formData.append("images", file, `image${index}.jpg`);
    });

    try {
        const response = await fetch('http://127.0.0.1:8000/stitch_images/', { // Replace with your backend URL
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const blob = await response.blob();
            const blobURL = URL.createObjectURL(blob);

            // Display the received stitched image
            const stitchedImagePreview = document.getElementById('stitchedPreview');
            stitchedImagePreview.src = blobURL;
            stitchedImagePreview.style.display = 'block';

            // Create a download button
            const downloadButton = document.getElementById('downloadButton');
            downloadButton.href = blobURL;
            downloadButton.download = "stitched_image.jpg";
            downloadButton.style.display = 'block';

        } else {
            alert("error during stitching. Try different order of images or check if images show the same thing");
            console.error("Failed to receive stitched image.");
        }
    } catch (error) {
        alert("error during stitching. Try different order of images or check if images show the same thing");
        console.error("Error:", error);
    }
});


function dataURItoBlob(dataURI) {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
}