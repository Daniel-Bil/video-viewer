document.addEventListener("DOMContentLoaded", () => {
    const csrfToken = getCookie("csrftoken"); // Get CSRF token from cookies

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + '=') {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Update profile image dynamically
    function updateProfileImage(action) {
        // Extract the username from the current URL
        const username = window.location.pathname.split('/')[2];

        // Construct the full URL with the username
        const url = `/profile/update_profile_image/`;

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ action: action }),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to update image');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const profileImage = document.getElementById('profile-image');
                    profileImage.src = data.image_url; // Update the image src dynamically
                    console.log("assign new image")
                    console.log(`${data.image_url}`)
                }
            })
            .catch(error => console.error('Error:', error));
    }

    // Add event listeners to buttons
    document.getElementById('prev-btn').addEventListener('click', () => {
        updateProfileImage('prev');
    });

    document.getElementById('next-btn').addEventListener('click', () => {
        updateProfileImage('next');
    });
});
