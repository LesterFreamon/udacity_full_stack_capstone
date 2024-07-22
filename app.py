from datetime import datetime  # Correct import statement
import os
import logging

import boto3
import cv2
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for, redirect, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_principal import Principal, PermissionDenied
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import db, Image, ImageSegment, User, Role, init_roles  # Import db and Image from models.py
from auth import setup_security, admin_permission, \
    admin_or_user_permission  # Import setup_security and permissions from auth.py
from utils import create_segmentation_layer, create_rgba_image, combine_two_images

# add logger
logging.basicConfig(level=logging.INFO)

load_dotenv()

MAX_IMAGES = 10
app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
setup_security(app)

db.init_app(app)  # Initialize db with the app
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'  # Specify the view which handles logins

principal = Principal(app)
setup_security(app)


def download_model():
    s3 = boto3.client('s3',
                      aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    bucket_name = 'heroku_s3_access'
    object_key = 'sam_vit_b_01ec64.pth'
    this_path = os.path.dirname(os.path.abspath(__file__))
    ai_model_path = os.path.join(this_path, 'ai_model')

    # Ensure the AI model directory exists
    os.makedirs(ai_model_path, exist_ok=True)

    this_path = os.path.dirname(os.path.abspath(__file__))
    download_path = os.path.join(ai_model_path, 'sam_vit_b_01ec64.pth')

    try:
        s3.download_file(bucket_name, object_key, download_path)
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


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.errorhandler(403)
def role_required(e: PermissionDenied):
    # Custom message depending on the endpoint or required role
    logging.error(f"Permission denied: {e}")
    required_role = 'user'  # Customize as necessary
    for need in e.description.needs:
        if need.value == 'admin':
            required_role = 'admin'

    return jsonify(error=f"You need to be a {required_role} role to do that"), 403


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            logging.info("User logged in")
            login_user(user)
            return redirect(url_for('index'))
        else:
            output_message = "Wrong username or password"
            logging.error(output_message)
            flash(output_message, 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_name = request.form['role']  # Assuming role name is passed from form

        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return render_template('register.html')

        # Check for role and create user with roles
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash(f'Role {role_name} not found!', 'error')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, roles=[role])
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        flash('User has been registered!')
        return redirect(url_for('index'))  # Redirect to the homepage or dashboard

    return render_template('register.html')


@app.route('/')
def index():
    if current_user.is_authenticated:
        roles_list = ', '.join([role.name for role in current_user.roles])
    else:
        roles_list = 'No roles'
    return render_template('index.html', roles_list=roles_list)


@app.route('/get-image/<int:image_id>', methods=['GET'])
def get_image(image_id):
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404

    image_segment = ImageSegment.query.filter_by(image_id=image_id).first()
    processed_filename = None
    if image_segment:
        processed_filename = image_segment.processed_filename

    response = {
        'id': image.id,
        'original': image.filename,
        'segmented': processed_filename
    }
    return jsonify(response), 200


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
@admin_permission.require(http_exception=403)  # Enforce admin permissions
def delete_image(image_id):
    # Find the image and its segment
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404

    image.active = False
    image.deleted_at = datetime.utcnow()
    db.session.commit()

    image_segment = ImageSegment.query.filter_by(image_id=image_id).first()

    # Delete image files from filesystem
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
        if image_segment and image_segment.processed_filename:
            os.remove(os.path.join(app.config['PROCESSED_FOLDER'], image_segment.processed_filename))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Image and its segment deleted successfully'}), 200


@app.route('/upload', methods=['POST'])
@admin_or_user_permission.require(http_exception=403)
def upload_image():
    file = request.files['image']
    if file:
        # Ensure only MAX_IMAGES images are stored, handle the oldest if more
        if Image.query.filter_by(active=True).count() >= MAX_IMAGES:
            oldest_image = Image.query.filter_by(active=True).order_by(Image.timestamp).first()
            oldest_image_id = oldest_image.id
            delete_image(oldest_image_id)

        timestamp = datetime.utcnow().isoformat()
        filename = f"{timestamp}-{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_image = Image(filename=filename, filepath=filepath)
        db.session.add(new_image)
        db.session.commit()

        # Generate a URL for the uploaded file
        file_url = url_for('uploaded_file', filename=filename, _external=True)

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


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if 'combined' in filename:
        return send_from_directory(app.config['PROCESSED_FOLDER'], filename)
    else:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/apply-sam/<int:image_id>', methods=['GET'])
@admin_or_user_permission.require(http_exception=403)
def apply_sam(image_id):
    logging.info("apply-sam")
    image = Image.query.get(image_id)
    if image.active:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)

        # Check if the file exists to avoid errors
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        # Open the image using OpenCV
        original_image = cv2.imread(file_path)
        if original_image is None:
            return jsonify({'error': 'Error opening image file'}), 500

        # delete previous segment data
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

        # Save the combined image
        processed_filename = f"combined-{os.path.basename(file_path)}"
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
        cv2.imwrite(processed_path, cv2.cvtColor(combined_image, cv2.COLOR_RGB2BGR))  # Save in BGR format

        logging.info("Masked image saved successfully")

        file_url = url_for('uploaded_file', filename=processed_filename, _external=True)

        # Store segment data
        new_segment = ImageSegment(
            image_id=Image.query.filter_by(filename=os.path.basename(file_path)).first().id,
            processed_filename=processed_filename,
            num_segments=len(masks_info)
        )

        logging.info("Segment data stored successfully")
        db.session.add(new_segment)
        db.session.commit()

        return jsonify({'processedUrl': file_url}), 200
    return jsonify({'error': 'No image URL provided'}), 400


# Make sure to call this function in an application context
# For example, if running in a Flask shell, just call print_constraints()
if __name__ == '__main__':
    app.run(debug=True)
