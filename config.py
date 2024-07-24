import os
from dotenv import load_dotenv
load_dotenv()  # This loads the env variables from .env file

class Config:
    UPLOAD_FOLDER = 'images/uploads/'
    PROCESSED_FOLDER = 'images/segments/'
    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE = True
    HOSTNAME = os.environ.get('HOSTNAME', 'localhost')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DB_USERNAME = os.environ.get('DB_USERNAME')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_PORT = os.environ.get('DB_PORT')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{HOSTNAME}:{DB_PORT}/postgres')
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MODEL_TYPE = "vit_b"
    CHECKPOINT_PATH = "ai_model/sam_vit_b_01ec64.pth"
    BUCKET_NAME = "ai-sam-models"
    S3_REGION = "us-east-1"
    S3_LOCATION = f'http://{BUCKET_NAME}.s3.amazonaws.com/'
    WTF_CSRF_ENABLED = False  # Disable CSRF protection


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing
