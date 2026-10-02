from pydantic import BaseModel, EmailStr

class WaitlistJoinRequest(BaseModel):
    email: EmailStr | None = None