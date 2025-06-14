from typing import Any
from pydantic import BaseModel


class User(BaseModel):
    id: str | None
    email: str | None
    name: str | None
    given_name: str | None
    family_name: str | None
    picture: str | None