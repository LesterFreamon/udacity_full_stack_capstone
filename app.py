from datetime import datetime  # Correct import statement
import os
import logging
from io import BytesIO

import base64
import boto3
import cv2

from dotenv import load_dotenv
from flask import jsonify
from flask_security import (
    roles_required, SQLAlchemyUserDatastore, Security, current_user, login_user, url_for_security, roles_accepted
)
from werkzeug.security import generate_password_hash
from flask_security.signals import user_registered

import numpy as np
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_migrate import Migrate
from aws_utils import upload_file_to_s3, download_file_from_s3, delete_file_from_s3
from config import Config
from models import db, Image, ImageSegment, AppUser, Role, init_roles  # Import db and Image from models.py
from utils import create_segmentation_layer, create_rgba_image, combine_two_images
from werkzeug.security import check_password_hash

# add logger
logging.basicConfig(level=logging.INFO)

load_dotenv()

app = Flask(__name__)

app.config.from_object(Config)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SECURITY_REGISTERABLE'] = True  # Enable registration
app.config['SECURITY_CONFIRMABLE'] = True  # If you want email confirmation

db.init_app(app)  # Initialize db with the app
migrate = Migrate(app, db)

user_datastore = SQLAlchemyUserDatastore(db, AppUser, Role)
security = Security(app, user_datastore)

s3_client = boto3.client('s3',
                         aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                         aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                         region_name='us-east-1')


def download_model():
    """Download the model from S3 if it does not exist locally."""
    logging.info("Downloading model")
    this_path = os.path.dirname(os.path.abspath(__file__))
    ai_model_path = os.path.join(this_path, 'ai_model')
    object_key = 'sam_vit_b_01ec64.pth'

    # check if the model already exists
    if os.path.exists(os.path.join(ai_model_path, object_key)):
        logging.info("Model already exists")
    else:
        logging.info("Model does not exist")
        # Ensure the AI model directory exists
        os.makedirs(ai_model_path, exist_ok=True)
        download_path = os.path.join(ai_model_path, 'sam_vit_b_01ec64.pth')

        try:
            s3_client.download_file(app.config['BUCKET_NAME'], object_key, download_path)
            logging.info("Model downloaded successfully")
        except Exception as e:
            logging.error(f"Failed to download model: {e}")


# Download the model file
download_model()

# Initialize roles
with app.app_context():
    # if the db has not been created, create it
    db.create_all()
    init_roles()

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Initialize SAM model
sam_model = sam_model_registry[app.config['MODEL_TYPE']](checkpoint=app.config['CHECKPOINT_PATH'])
mask_generator = SamAutomaticMaskGenerator(sam_model)

user_registered.connect_via(app)


@app.route('/')
def index():
    return render_template('index.html', user=current_user)


@app.route('/custom_register', methods=['GET', 'POST'])
def custom_register():
    if request.method == 'POST':
        form_data = request.form
        username = form_data.get('username')
        password = form_data.get('password')
        role_name = form_data.get('role')

        existing_user = AppUser.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'error')
            return redirect(url_for('custom_register'))

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash(f'Role {role_name} not found!', 'error')
            return redirect(url_for('custom_register'))

        hashed_password = generate_password_hash(password)
        new_user = user_datastore.create_user(username=username, password=hashed_password, roles=[role])
        db.session.add(new_user)
        db.session.commit()

        # Log in the new user
        login_user(new_user)

        flash('User has been registered!')
        return redirect(url_for('index'))

    return render_template('security/register_user.html')

@app.route('/custom_login', methods=['POST'])
def custom_login():

    username = request.form.get('username')
    password = request.form.get('password')


    if not username or not password:
        flash('Username or password cannot be empty')
        return redirect(url_for_security('login'))

    existing_user = AppUser.query.filter_by(username=username).first()

    if existing_user and check_password_hash(existing_user.password, password):
        login_user(existing_user)
        return redirect(url_for('index'))  # Redirect to a secure page after login

    flash('Invalid username or password')
    return redirect(url_for_security('login'))

@user_registered.connect_via(app)
def user_registered_sighandler(sender, user, confirm_token):
    logging.info("User registered")
    role_name = request.form['role']
    role = Role.query.filter_by(name=role_name).first()
    if role:
        user_datastore.add_role_to_user(user, role)
        db.session.commit()
    return render_template('register.html')


@app.route('/get-image-data-from-id/<int:image_id>', methods=['GET'])
def get_image_data_id(image_id):
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404

    image_segment = ImageSegment.query.filter_by(image_id=image_id).first()
    processed_filename = None
    if image_segment:
        processed_filename = image_segment.processed_filename

    response = {
        'id': image.id,
        'original': image.filepath,
        'segmented': processed_filename
    }
    return jsonify(response), 200


@app.route('/get-image/<path:filename>', methods=['GET'])
def get_image(filename):
    logging.info(current_user.roles)

    try:
        # Download the file from S3
        logging.info("Downloading file from S3")
        file = download_file_from_s3(s3_client, filename, app.config['BUCKET_NAME'])
        logging.info("File downloaded successfully")

        # Encode the file in Base64
        base64_encoded_data = base64.b64encode(file.getvalue()).decode('utf-8')
        image_data = f"data:image/jpeg;base64,{base64_encoded_data}"

        # Prepare metadata
        metadata = s3_client.head_object(Bucket=app.config['BUCKET_NAME'], Key=filename)
        logging.info("Metadata fetched successfully")
        content_type = metadata['ContentType']
        size = metadata['ContentLength']

        response = {
            'filename': filename,
            'imageData': image_data,
            'contentType': content_type,
            'size': size
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get-image-list', methods=['GET'])
def get_image_list():
    images = Image.query.filter_by(active=True).all()  # Fetching all active images
    image_list = []
    for image in images:
        image_segment = ImageSegment.query.filter_by(image_id=image.id).first()
        if image_segment:
            processed_filename = image_segment.processed_filename
            image_list.append({
                'id': image.id,
                'original': image.filename,
                'segmented': processed_filename
            })
        else:
            image_list.append({
                'id': image.id,
                'original': image.filename,
                'segmented': None
            })
    return jsonify(image_list), 200


@app.route('/delete-image/<int:image_id>', methods=['DELETE'])
@roles_required('admin')  # Requires that the currently logged-in user has the 'admin' role
def delete_image(image_id):
    # Find the image and its segment
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404

    image.active = False
    image.deleted_at = datetime.utcnow()
    db.session.commit()

    image_segment = ImageSegment.query.filter_by(image_id=image_id).first()

    # Delete image files from S3
    try:
        error = delete_file_from_s3(s3_client, image.filepath, app.config['BUCKET_NAME'])
        if error:
            return jsonify({'error': error}), 500

        if image_segment and image_segment.processed_filename:
            error = delete_file_from_s3(s3_client, image_segment.processed_filename, app.config['BUCKET_NAME'])
            if error:
                return jsonify({'error': error}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Image and its segment deleted successfully'}), 200


@app.route('/upload', methods=['POST'])
@roles_accepted('user', 'admin')
def upload_image():
    logging.info("upload-image")
    file = request.files['image']
    if file:
        logging.info("File received")

        timestamp = datetime.utcnow().isoformat()
        filename = f"{timestamp}-{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        logging.info("Uploading file to S3")

        file_url = upload_file_to_s3(s3_client, file, filepath, app.config['BUCKET_NAME'])

        logging.info("File uploaded to S3 successfully to %s", file_url)

        new_image = Image(filename=filename, filepath=filepath)
        db.session.add(new_image)
        db.session.commit()

        response = {
            'id': new_image.id,
            'filename': filename,
            'filepath': filepath,
            'url': file_url,
            'timestamp': timestamp,
            'active': new_image.active
        }
        return jsonify(response), 200

    return jsonify({'error': 'No file provided'}), 400


@app.route('/apply-sam/<int:image_id>', methods=['GET'])
@roles_accepted('user', 'admin')
def apply_sam(image_id):
    logging.info("apply-sam")
    image = Image.query.get(image_id)
    if image.active:

        file_obj = download_file_from_s3(s3_client, image.filepath, app.config['BUCKET_NAME'])

        # Check if the file exists to avoid errors
        if file_obj is None:
            return jsonify({'error': 'File not found in S3'}), 404

        # Open the image using OpenCV
        file_bytes = np.asarray(bytearray(file_obj.read()), dtype=np.uint8)
        original_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if original_image is None:
            return jsonify({'error': 'Error opening image file'}), 500

        # delete previous segment images
        ImageSegment.query.filter_by(image_id=image_id).delete()
        db.session.commit()

        # Convert image to RGB if necessary (OpenCV loads in BGR)
        original_image_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
        logging.info("Image opened successfully")

        # Apply the SAM model to get the mask
        # Assuming `mask_generator` is defined elsewhere and properly configured
        masks_info = mask_generator.generate(original_image_rgb)

        if not masks_info:
            return jsonify({'error': 'No masks generated'}), 500

        logging.info("Mask generated successfully")

        # Generate the combined image with annotations
        masked_image = create_segmentation_layer(masks_info, original_image_rgb)

        logging.info("Masked image generated successfully")

        rgba_image = create_rgba_image(original_image_rgb)

        combined_image = combine_two_images(rgba_image, masked_image)

        # Save the combined image to a BytesIO object
        _, img_encoded = cv2.imencode('.jpg', cv2.cvtColor(combined_image, cv2.COLOR_RGB2BGR))
        img_io = BytesIO(img_encoded)

        # Create a filename and upload to S3
        timestamp = datetime.utcnow().isoformat()
        processed_filename = f"combined-{timestamp}.jpg"
        filepath = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)

        img_io.seek(0)  # Seek to the start of the BytesIO object

        file_url = upload_file_to_s3(s3_client, img_io, filepath, app.config['BUCKET_NAME'])
        logging.info("Masked image uploaded to S3 successfully")

        # Store segment images
        new_segment = ImageSegment(
            image_id=image.id,
            processed_filename=filepath,
            num_segments=len(masks_info)
        )

        logging.info("Segment images stored successfully")
        db.session.add(new_segment)
        db.session.commit()

        return jsonify({'processedUrl': file_url}), 200
    return jsonify({'error': 'No image URL provided'}), 400


# Make sure to call this function in an application context
# For example, if running in a Flask shell, just call print_constraints()
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Default to 5000 if no PORT variable is set
    app.run(host='0.0.0.0', port=port, debug=True)
