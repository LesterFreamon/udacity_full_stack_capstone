import os
class Config:
    UPLOAD_FOLDER = 'data/uploads/'
    PROCESSED_FOLDER = 'data/segments/'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MODEL_TYPE = "vit_b"
    CHECKPOINT_PATH = "ai_model/sam_vit_b_01ec64.pth"


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing
