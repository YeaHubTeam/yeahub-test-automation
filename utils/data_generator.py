import random
import string
import uuid

from faker import Faker

faker = Faker()


class DataGenerator:
    @staticmethod
    def random_username():
        return faker.name()

    @staticmethod
    def random_password():
        """Пароль для UI/API: длина и набор символов без «спорных» знаков (^| и т.п.)."""
        lower = random.choice(string.ascii_lowercase)
        upper = random.choice(string.ascii_uppercase)
        digit = random.choice(string.digits)
        special = random.choice("@#$%&*-_+=.")
        alphabet = string.ascii_letters + string.digits + "@#$%&*-_+=."
        remaining_length = random.randint(8, 14)
        remaining = "".join(random.choices(alphabet, k=remaining_length))
        parts = list(lower + upper + digit + special + remaining)
        random.shuffle(parts)
        return "".join(parts)

    @staticmethod
    def random_email():
        return faker.email()

    @staticmethod
    def unique_email(domain: str = "example.com") -> str:
        """Уникальный email для UI signUp — без коллизий faker @example.com на stage."""
        return f"autotest-{uuid.uuid4().hex}@{domain}"

    @staticmethod
    def unique_username(prefix: str = "AutoTest") -> str:
        return f"{prefix} {uuid.uuid4().hex[:12]}"

    @staticmethod
    def random_phone():
        number_phone = "".join(random.choices(string.digits, k=10))
        return f"+{number_phone}"

    @staticmethod
    def random_country():
        return faker.country()

    @staticmethod
    def random_city():
        return faker.city()

    @staticmethod
    def random_birthday():
        birthday = faker.date_of_birth(minimum_age=16, maximum_age=100)
        return birthday.strftime("%Y-%m-%d")

    @staticmethod
    def random_address():
        return faker.address()

    @staticmethod
    def random_avatar_url():
        return faker.image_url()
