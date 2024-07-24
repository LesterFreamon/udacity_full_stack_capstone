# Image Segmentation Web Application

This project is a web application that allows users to upload images and apply Meta's SAM (Segment Anything Model) for image segmentation. The application provides a user-friendly interface for uploading images, applying the SAM model, and viewing segmented results.

## Project Structure

```
.
├── Procfile
├── ai_model
│ └── sam_vit_b_01ec64.pth
├── app.py
├── auth.py
├── config.py
├── data
│ ├── segments
│ └── uploads
├── example_images
├── instance
│ └── site.db
├── manage.py
├── migrations
├── models.py
├── notebooks
│ ├── init.py
│ └── explore.ipynb
├── requirements.txt
├── runtime.txt
├── setup.sh
├── static
│ ├── css
│ │ └── styles.css
│ ├── images
│ │ └── no_image_available.png
│ └── js
├── templates
│ ├── base.html
│ ├── index.html
│ ├── login.html
│ └── register.html
├── tests
│ ├── init.py
│ └── test_endpoints.py
└── utils.py
```

## Features

- **User Authentication**: Users can register, log in, and log out.
- **Image Upload**: Users can upload images to be processed by the SAM model.
- **Image Segmentation**: The SAM model processes the uploaded images and generates segmented results.
- **Image Management**: Users can view and delete their uploaded images and segmented results.

## Setup and Installation

### Prerequisites

- Python 3.8+
- Virtual Environment (optional but recommended)

### Installation

1. **Clone the Repository**

```bash
   git clone https://github.com/your-username/image-segmentation-app.git
   cd image-segmentation-app
   ```
   
2. **Create a Virtual Environment**

   ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
   ```

3. **Install the Required Packages**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**

   Create a `.env` file in the root directory and add the following environment variables:

   ```bash
   SECRET_KEY=your_secret_key
   SQLALCHEMY_DATABASE_URI=sqlite:///instance/site.db
   UPLOAD_FOLDER=images/uploads
   PROCESSED_FOLDER=images/segments
   MODEL_TYPE=sam_vit_b
   CHECKPOINT_PATH=ai_model/sam_vit_b_01ec64.pth
    ```
   
5. **Run Database Migrations**

   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. **Run the Application**

   ```bash
    python app.py
    ```

The application will be available at http://127.0.0.1:5000.

## Usage
1. Register an Account

Navigate to http://127.0.0.1:5000/register and create a new account.

2. Log In

Navigate to http://127.0.0.1:5000/login and log in with your credentials.

3. Upload Images

Use the interface to upload images. The images will be processed by the SAM model, and the segmented results will be displayed.

4. Manage Images

View and delete your uploaded images and segmented results as needed.

### Running Tests
To run the tests, use the following command:

```bash
pytest
```

### Deployment
To deploy the application, you can use platforms like Heroku. Make sure to set up the required environment variables on the platform you choose.

### Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

### License
This project is licensed under the MIT License.

### Acknowledgements
* Meta's SAM Model for the image segmentation capabilities.
* Flask and its extensions for providing the framework and utilities.
* Alembic for handling database migrations.