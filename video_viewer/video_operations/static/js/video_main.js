const form = document.getElementById('videoUploadForm');
const status = document.getElementById('status');
const videoPreview = document.getElementById('videoPreview');

form.addEventListener('submit', async (event) => {
    event.preventDefault(); // Prevent the form from submitting normally

    const fileInput = document.getElementById('videoFile');
    const file = fileInput.files[0];

    if (!file) {
        status.textContent = "Please select a file.";
        return;
    }

    // Collect selected operations
    const operations = [];
    const labels = document.querySelectorAll('.neomorphic-checkbox'); // Get all labels with the class
    labels.forEach((label) => {
        const input = label.previousElementSibling; // Get the <input> at the same level as the label
        if (input && input.checked) {
            const span = label.querySelector('span'); // Get the <span> inside the label
            if (span) {
                operations.push(span.textContent.trim()); // Add the text to the operations array
            }
        }
    });

    // Prepare FormData for upload
    const formData = new FormData();
    formData.append('video', file);
    formData.append('operations', JSON.stringify(operations));

    try {
        status.textContent = "Uploading...";

        const response = await fetch('http://127.0.0.1:8000/upload/', { // Replace with your backend URL
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            // Check the response content type
            const contentType = response.headers.get('Content-Type');
            const blob = await response.blob();
            const blobURL = URL.createObjectURL(blob);

            if (contentType === 'image/gif') {
                // Show GIF in the <img> element
                const gifPreview = document.getElementById('gifPreview');
                gifPreview.src = blobURL;
                gifPreview.style.display = 'block';

                // Hide the <video> element
                const videoPreview = document.getElementById('videoPreview');
                videoPreview.style.display = 'none';
            } else if (contentType === 'video/mp4') {
                // Show video in the <video> element
                const videoPreview = document.getElementById('videoPreview');
                videoPreview.src = blobURL;
                videoPreview.style.display = 'block';

                // Hide the <img> element
                const gifPreview = document.getElementById('gifPreview');
                gifPreview.style.display = 'none';
            }

            status.textContent = "Processing complete!";

        } else {
            status.textContent = "Upload failed. Please try again.";
        }
    } catch (error) {
        console.error("Error:", error);
        status.textContent = "Error occurred while uploading.";
    }
});