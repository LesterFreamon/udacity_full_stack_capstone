document.addEventListener('DOMContentLoaded', function () {
    let dropArea = document.getElementById('drop-area');
    if (dropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
            if (eventName === 'dragover') {
                dropArea.classList.add('hover');
            } else {
                dropArea.classList.remove('hover');
            }
        });
        dropArea.addEventListener('drop', handleDrop, false);
        console.log('Drop area ready for interaction.');
    } else {
        console.log('Drop area element not found on this page.');
    }

    const imageDropdown = document.getElementById('imageDropdown');
    if (imageDropdown) {
        imageDropdown.addEventListener('click', loadImages);
        console.log('Image dropdown ready for interaction.');
    } else {
        console.log('Image dropdown element not found on this page.');
    }
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
                   alert("you do not have the proper permissions"); // Only show alert if there's an error
                }
                throw new Error('Network response was not ok.');
            }
            else {
                return response;
            }
        })
    .then(data => {
        // Assuming `data.filename` contains the filename of the uploaded image
        if (!data.filename) {
            throw new Error('Filename not provided in the upload response');
        }
        // Use FileReader to read the file and display it
        const reader = new FileReader();
        reader.onload = function(e) {
            cleanGallery(); // Clear existing images
            displayImage(e.target.result, 'original-gallery'); // Display the original image using result from FileReader
        };
        reader.onerror = function() {
            console.error('Error reading file.');
        };
        reader.readAsDataURL(file); // This reads the file as a data URL encoding of the base64 image
    })
    .catch(error => console.error('Error during upload:', error));
}

function displayImage(imageData, galleryId) {
    let gallery = document.getElementById(galleryId);
    let imgContainer = document.createElement('div');
    imgContainer.className = 'image-container';
    let img = document.createElement('img');
    // check if imageUrl is null
    if (!imageData) {
        img.src = 'static/images/no_image_available.png';
    } else {
        img.src = imageData;
    }
    imgContainer.appendChild(img);
    gallery.appendChild(imgContainer);
}


function loadImages() {
    fetch('/get-image-list')
        .then(response => {
            if (!response.ok) {
                if (response.status === 403) {
                   alert("you do not have the proper permissions"); // Only show alert if there's an error
                }
                throw new Error('Network response was not ok.');
            }
            else {
                return response;
            }
        })
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
    cleanGallery();  // Assuming this function clears the display area
    // Fetching metadata first
    fetch(`/get-image-data-from-id/${imageId}`)
        .then(response => response.json())
        .then(data => {
            if (!data.original && !data.segmented) {
                throw new Error('No images available');
            }
            // If there's an original image, fetch and display it
            if (data.original) {
                fetchAndDisplayImage(data.original, 'original-gallery');
            }
            // If there's a segmented image, fetch and display it
            if (data.segmented) {
                fetchAndDisplayImage(data.segmented, 'segmented-gallery');
            }
            else {
                displayImage(null, 'segmented-gallery');
            }
        })
        .catch(error => console.error('Error displaying image:', error));
}

function fetchAndDisplayImage(filename, galleryId) {
    fetch(`/get-image/${filename}`)
        .then(response => response.json())
        .then(data => {
            displayImage(data.imageData, galleryId);
        })
        .catch(error => console.error('Error fetching image data:', error));
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
                   alert("you do not have the proper permissions"); // Only show alert if there's an error
                }
            }
            else {
                return response.json().then(data => {
                    console.log('Success:', data); // Log success without alerting
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred: ' + error.message); // Alert any fetch or network errors
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

function removeLoader() {
    const segmentedGallery = document.getElementById('segmented-gallery');
    let loader = document.querySelector('.loader');
    if (loader) {
        segmentedGallery.removeChild(loader);
                // Clear the text

        segmentedGallery.removeChild(segmentedGallery.lastChild);

    }
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
                    removeLoader();
                   alert("you do not have the proper permissions"); // Only show alert if there's an error
                }
                throw new Error('Network response was not ok.');
            }
            else {
                return response;
            }
        })
        .then(data => {
            // Display the segmented image
            showSelectedImage();
        })
        .catch(error => console.error('Error applying SAM:', error));
}