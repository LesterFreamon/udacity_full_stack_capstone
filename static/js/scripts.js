document.addEventListener('DOMContentLoaded', function () {
    // Handle file selection and drop events
    let dropArea = document.getElementById('drop-area');
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        eventName === 'dragover' ? dropArea.classList.add('hover') : dropArea.classList.remove('hover');
    });
    dropArea.addEventListener('drop', handleDrop, false);

    // Initialize image dropdown
    const imageDropdown = document.getElementById('imageDropdown');
    imageDropdown.addEventListener('click', loadImages);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    let dt = e.dataTransfer;
    let files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    ([...files]).forEach(uploadFile);
}
function handleForbiddenResponse(response) {
    return response.json().then(data => {
        alert(data.error);  // Display the custom error message from server
    });
}
function cleanGallery() {
    const originalGallery = document.getElementById('original-gallery');
    const segmentedGallery = document.getElementById('segmented-gallery');

    originalGallery.innerHTML = '';  // Clear previous images
    segmentedGallery.innerHTML = ''; // Clear previous images

    while (segmentedGallery.firstChild) {
        segmentedGallery.removeChild(segmentedGallery.firstChild);
    }

    while (originalGallery.firstChild) {
        originalGallery.removeChild(originalGallery.firstChild);
    }

}


function uploadFile(file) {
    let formData = new FormData();
    formData.append('image', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) {
                if (response.status === 403) {
                    return handleForbiddenResponse(response);
                }
                throw new Error('Network response was not ok.');
            }
            return response.json();
        })
        .then(data => {
            if (data.url) {
                cleanGallery(); // Clear existing images
                displayImage(data.filename, 'original-gallery'); // Display the original image
            } else {
                console.error('Error uploading image:', data.error);
            }
        })
        .catch(error => console.error('Error uploading image:', error));
}

function displayImage(imageUrl, galleryId) {
    let gallery = document.getElementById(galleryId);
    let imgContainer = document.createElement('div');
    imgContainer.className = 'image-container';

    let img = document.createElement('img');
    // check if imageUrl is null

    if (!imageUrl) {
        img.src = 'static/images/no_image_available.png'
    } else {
        img.src = `/uploads/${imageUrl}`;
    }
    imgContainer.appendChild(img);
    gallery.appendChild(imgContainer);
}


function loadImages() {
    fetch('/get-image-list')
        .then(response => response.json())
        .then(images => {
            const dropdown = document.getElementById('imageDropdown');
            dropdown.innerHTML = '<option value="">Select an image...</option>'; // Clear existing options
            images.forEach(image => {
                let option = new Option(image.original, image.id);
                dropdown.add(option);
            });
        })
        .catch(error => console.error('Error loading images:', error));
}

function showSelectedImage() {
    let imageId = document.getElementById('imageDropdown').value;
    if (!imageId) {
        alert('Please select an image to view.');
        return;
    }
    cleanGallery();
    // Assuming you have an endpoint to fetch an image by ID
    fetch(`/get-image/${imageId}`)
        .then(response => response.json())
        .then(data => {
            // Display the selected original image
            displayImage(data.original, 'original-gallery');
            if (data.segmented) {
                displayImage(data.segmented, 'segmented-gallery');
            } else {
                displayImage(null, 'segmented-gallery');
            }
        })
        .catch(error => console.error('Error displaying image:', error));
}

function deleteSelectedImage() {
    let imageId = document.getElementById('imageDropdown').value;
    if (!imageId) {
        alert('Please select an image to delete.');
        return;
    }

    if (confirm('Are you sure you want to delete this image?')) {
        fetch(`/delete-image/${imageId}`, {
            method: 'DELETE'
        })
            .then(response => {
        if (!response.ok) {
            if (response.status === 403) {
                return handleForbiddenResponse(response);
            }
            throw new Error('Network response was not ok.');
        }
        return response.json();
    })
    .then(data => {
        console.log('Success:', data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
    }
}

function createLoader() {
    let loader = document.createElement('div');
    loader.className = 'loader';
    return loader;
}

function addLoader() {
    // Clear the gallery and display loader
    const segmentedGallery = document.getElementById('segmented-gallery');
    segmentedGallery.innerHTML = ''; // Clear existing images
    let loader = createLoader();
    segmentedGallery.appendChild(loader);
    let text = document.createElement('div');
    text.innerHTML = 'This will take about a minute';
    segmentedGallery.appendChild(text);

}

function applySam() {
    // Display loader
    let imageId = document.getElementById('imageDropdown').value;
    if (!imageId) {
        alert('Please select an image to apply SAM.');
        return;
    }
    addLoader();

    fetch(`/apply-sam/${imageId}`)
        .then(response => {
            if (!response.ok) {
                if (response.status === 403) {
                    return handleForbiddenResponse(response);
                }
                throw new Error('Network response was not ok.');
            }
            return response.json();
        })
        .then(data => {
            // Display the segmented image
            showSelectedImage();
        })
        .catch(error => console.error('Error applying SAM:', error));
}