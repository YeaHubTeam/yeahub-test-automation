import random
import string

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
        year = random.randint(1950, 2007)
        month = faker.month()
        day = faker.day_of_month()
        return f"{year}-{month}-{day}"

    @staticmethod
    def random_address():
        return faker.address()

    @staticmethod
    def random_avatar_url():
        return faker.image_url()
