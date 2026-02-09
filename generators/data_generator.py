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
        letters = random.choice(string.ascii_letters)
        digits = random.choice(string.digits)

        special_chars = "?@#$%^&*|:"
        all_chars = string.ascii_letters + string.digits + special_chars
        remaining_length = random.randint(6, 18)
        remaining_chars = "".join(random.choices(all_chars, k=remaining_length))

        password = list(letters + digits + remaining_chars)
        random.shuffle(password)

        return "".join(password)

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
