from generators.data_generator import DataGenerator
from utils.decorators import Decorator


class AuthPayloads:
    @staticmethod
    @Decorator.with_overrides
    def signup_full() -> dict:
        """Данные для регистрации пользователя"""
        payloads = {
            "username": DataGenerator.random_username(),
            "password": DataGenerator.random_password(),
            "email": DataGenerator.random_email(),
            "phone": DataGenerator.random_phone(),
            "country": DataGenerator.random_country(),
            "city": DataGenerator.random_city(),
            "birthday": DataGenerator.random_birthday(),
            "address": DataGenerator.random_address(),
            "avatarUrl": DataGenerator.random_avatar_url(),
            "refId": "",
        }
        return payloads
