import re
from pydantic import BaseModel, EmailStr, ValidationError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[+()\d\-\s]{6,}$")

class RequestModel(BaseModel):
    name: str
    company: str | None = None
    email: EmailStr
    contact: str
    req_type: str
    description: str
    budget: str | None = None
    # ветвления
    ai_data: str | None = None
    ai_dataset: str | None = None
    web_auth: str | None = None
    web_integrations: str | None = None

def validate_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value or ""))

def validate_phone(value: str) -> bool:
    return bool(PHONE_RE.match(value or ""))
