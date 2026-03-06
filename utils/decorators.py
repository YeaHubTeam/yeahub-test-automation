class Decorator:
    @staticmethod
    def with_overrides(func):
        """Декоратор для обновления словаря"""

        def wrapper(*args, **kwargs):
            payload = func()
            if kwargs:
                payload.update(kwargs)
            return payload

        return wrapper
