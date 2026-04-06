from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """
    Базовая модель ответа API, к которому можно обращаться как с dict и как модель.

    """
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        from_attributes=True,
        strict=False
    )

    # --- dict-like интерфейс ---

    def __getitem__(self, key):
        """data["field"]"""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """data["field"] = value"""
        setattr(self, key, value)

    def __contains__(self, key):
        """'id' in data"""
        return hasattr(self, key) and getattr(self, key) is not None

    def get(self, key, default=None):
        """data.get("field")"""
        return getattr(self, key, default)

    def keys(self):
        return self.model_dump().keys()

    def values(self):
        return self.model_dump().values()

    def items(self):
        return self.model_dump().items()

    def to_dict(self):
        """Явное преобразование"""
        return self.model_dump()

    def __iter__(self):
        """Позволяет делать dict(model)"""
        return iter(self.model_dump().items())