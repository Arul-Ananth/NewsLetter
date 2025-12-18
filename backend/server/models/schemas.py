from pydantic import BaseModel, EmailStr

# Auth Schemas
class UserSignup(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# News Schemas
class NewsRequest(BaseModel):
    topic: str
    serper_api_key: str | None = None
    openai_api_key: str | None = None

class NewsResponse(BaseModel):
    topic: str
    content: str
    bill: dict

class FeedbackRequest(BaseModel):
    original_topic: str
    feedback_text: str
    sentiment: str