from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str = Field(...,min_length=3, max_length=50, description="The name of the user")
    email: EmailStr = Field(..., description="The email of the user")

class UserResponse(BaseModel):
    id: int = Field(..., description="The id of the user")
    name: str = Field(..., description="The name of the user")
    email: EmailStr = Field(..., description="The email of the user")
    
    model_config = {
        "from_attributes": True,
    }