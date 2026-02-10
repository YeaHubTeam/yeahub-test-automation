import pytest
import requests
import random
import string
from api.api_manager import ApiManager


@pytest.fixture(scope="session")
def session():
    session = requests.Session()
    yield session
    session.close()


@pytest.fixture(scope="session")
def api_manager(session):
    return ApiManager(session)


@pytest.fixture
def new_user_data():
    rand_str = "".join(random.choices(string.ascii_lowercase, k=10))
    email = f"test_user_{rand_str}@example.com"
    username = f"user_{rand_str}"
    password = "Password123!"
    phone = f"+1{random.randint(1000000000, 9999999999)}"
    return {
        "username": username,
        "password": password,
        "email": email,
        "phone": phone,
        "country": "USA",
        "city": "New York",
        "birthday": "1990-01-01",
        "address": "123 Main St",
        "avatarUrl": "http://example.com/avatar.jpg",
    }


@pytest.fixture
def registered_user(api_manager, new_user_data):
    response = api_manager.auth_api.register_user(new_user_data, expected_status=201)
    new_user_data["id"] = response.json().get("user", {}).get("id")
    new_user_data["token"] = response.json().get("access_token")
    return new_user_data


@pytest.fixture
def test_login(api_manager, registered_user):
    login_data = {
        "username": registered_user["email"],
        "password": registered_user["password"],
    }
    api_manager.auth_api.login_user(login_data, expected_status=201)
    api_manager.auth_api.authenticate(
        (registered_user["email"], registered_user["password"])
    )

    return registered_user


@pytest.fixture
def logout_user(test_login):
    return test_login


@pytest.fixture
def profile_user(test_login):
    return test_login


@pytest.fixture
def refresh_user(test_login):
    return test_login


@pytest.fixture
def send_reset_pass_user(registered_user):
    return registered_user


@pytest.fixture
def reset_password_user(registered_user):
    return registered_user


@pytest.fixture
def pass_exchange_user(test_login):
    return test_login


@pytest.fixture
def verify_email_user(registered_user):
    return registered_user


@pytest.fixture
def send_verification_email_user(test_login):
    return test_login


@pytest.fixture
def verification_user(send_verification_email_user):
    return send_verification_email_user
