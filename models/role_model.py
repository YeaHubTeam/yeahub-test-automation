from models.base_model import BaseResponse


class Permission(BaseResponse):
    id: int
    name: str


class Role(BaseResponse):
    id: int
    name: str
    permissions: list[Permission]