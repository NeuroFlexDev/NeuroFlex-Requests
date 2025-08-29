from pydantic import BaseModel, EmailStr

class RequestModel(BaseModel):
    name: str
    company: str | None = None
    email: EmailStr
    contact: str
    req_type: str
    description: str
    budget: str | None = None
