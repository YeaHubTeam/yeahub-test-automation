from generators.data_generator import DataGenerator


class AuthPayloads:

    @staticmethod
    def with_overrides(func):
        """Декоратор для обновления словаря"""
        def wrapper(*args, **kwargs):
            payload = func()
            if kwargs:
                payload.update(kwargs)
            return payload
        return wrapper

    @with_overrides
    @staticmethod
    def signup_full(**overides) -> dict:
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
            "refId": ""
        }
        return payloads

