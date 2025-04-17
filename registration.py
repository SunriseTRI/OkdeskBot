# registration.py (упрощенная версия)
import re
from pydantic import BaseModel, EmailStr, validator

class User(BaseModel):
    phone: str
    email: EmailStr
    username: str

    @validator("phone")
    def validate_phone(cls, v):
        if not re.match(r"^\+\d{11}$", v):
            raise ValueError("Неверный формат телефона")
        return v