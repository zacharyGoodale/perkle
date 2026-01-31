"""Authentication schemas."""
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """User registration request."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login request."""
    
    username: str  # Can be username or email
    password: str


class Token(BaseModel):
    """Token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request."""
    
    refresh_token: str


class UserResponse(BaseModel):
    """User info response."""
    
    id: str
    username: str
    email: str
    created_at: str
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response."""
    
    message: str
