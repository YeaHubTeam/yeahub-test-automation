import random
import string
from faker import Faker

faker = Faker()
class DataGenerator:

    @staticmethod
    def random_username(self):
        return faker.name()

    @staticmethod
    def random_password(self):
        letters = random.choice(string.ascii_letters)
        digits = random.choice(string.digits)

        special_chars = "?@#$%^&*|:"
        all_chars = string.ascii_letters + string.digits + special_chars
        remaining_length = random.randint(6, 18)
        remaining_chars = ''.join(random.choices(all_chars, k=remaining_length))

        password = list(letters + digits + remaining_chars)
        random.shuffle(password)

        return ''.join(password)

    @staticmethod
    def random_email(self):
        random_string = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=10))
        return f"{random_string}@yandex.ru"

    @staticmethod
    def random_phone(self):
        number_phone = ''.join(random.choices(string.digits, k=10))
        return f"+{number_phone}"

    @staticmethod
    def random_country(self):
        return faker.country()

    @staticmethod
    def random_city(self):
        return faker.city()

    @staticmethod
    def random_birthday(self):
        year = random.randint(1950, 2007)
        month = faker.month()
        day = faker.day_of_month()
        return f"{year}-{month}-{day}"

    @staticmethod
    def random_address(self):
        return faker.address()

    @staticmethod
    def random_avatar_url(self):
        return faker.image_url()
