import pytest
import requests
from api.api_manager import ApiManager
from utils.data_generator import DataGenerator


@pytest.fixture(scope="session")
def session():
    session = requests.Session()
    yield session
    session.close()


@pytest.fixture(scope="session")
def api_manager(session):
    return ApiManager(session)


@pytest.fixture
def test_user():
    email = DataGenerator.random_email()
    username = DataGenerator.random_username()
    password = DataGenerator.random_password()
    phone =  DataGenerator.random_phone()
    country=DataGenerator.random_country()
    city = DataGenerator.random_city()
    birthday = DataGenerator.random_birthday()
    address = DataGenerator.random_address()
    avatar_url= DataGenerator.random_avatar_url()
    return {
        "username": username,
        "password": password,
        "email": email,
        "phone": phone,
        "country": country,
        "city": city,
        "birthday": birthday,
        "address": address,
        "avatarUrl": avatar_url,
    }


@pytest.fixture
def registered_user(api_manager, test_user):
    response = api_manager.auth_api.register_user(test_user, expected_status=201)
    test_user["id"] = response.json().get("user", {}).get("id")
    test_user["token"] = response.json().get("access_token")
    return test_user



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


