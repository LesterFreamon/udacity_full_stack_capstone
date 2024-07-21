import os
import pytest
from app import app, db, init_roles
from models import User, Role
from werkzeug.security import generate_password_hash

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
TEST_IMAGE_PATH = os.path.join(THIS_FOLDER, 'test_image.jpg')


@pytest.fixture(scope='module')
def test_client():
    app.config.from_object('config.TestConfig')
    testing_client = app.test_client()

    with app.app_context():
        db.create_all()
        init_roles()

        # Create roles
        admin_role = Role.query.filter_by(name='admin').first()
        user_role = Role.query.filter_by(name='user').first()

        # Add roles if not exist
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)

        if not user_role:
            user_role = Role(name='user')
            db.session.add(user_role)

        db.session.commit()

        # Create users
        if not User.query.filter_by(username='adminuser').first():
            hashed_password = generate_password_hash('adminpassword')
            admin_user = User(username='adminuser', password=hashed_password, roles=[admin_role])
            db.session.add(admin_user)

        if not User.query.filter_by(username='testuser').first():
            hashed_password = generate_password_hash('testpassword')
            test_user = User(username='testuser', password=hashed_password, roles=[user_role])
            db.session.add(test_user)

        db.session.commit()

        yield testing_client
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='module')
def init_database():
    with app.app_context():
        db.create_all()
        init_roles()

        yield db
        db.session.remove()
        db.drop_all()


def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def test_index(test_client):
    response = test_client.get('/')
    assert response.status_code == 200


def test_login(test_client, init_database):
    response = login(test_client, 'testuser', 'testpassword')
    assert response.status_code == 200


def test_logout(test_client, init_database):
    test_client.post('/login', data=dict(
        username='testuser',
        password='testpassword'
    ), follow_redirects=True)
    response = test_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200


def test_register(test_client, init_database):
    response = test_client.post('/register', data=dict(
        username='newuser',
        password='newpassword',
        role='user'
    ), follow_redirects=True)
    assert response.status_code == 200


def test_get_image_list(test_client, init_database):
    response = test_client.get('/get-image-list')
    assert response.status_code == 200
    assert response.json == []  # Adjust this to match the actual format
