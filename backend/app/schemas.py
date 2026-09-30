from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    language: str = Field(default="mr", max_length=10)
    state: str = Field(default="", max_length=80)
    district: str = Field(default="", max_length=80)
    village: str = Field(default="", max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    role: str
    is_active: bool


class FarmerUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    language: str = Field(default="mr", max_length=10)
    state: str = Field(default="", max_length=80)
    district: str = Field(default="", max_length=80)
    village: str = Field(default="", max_length=120)
    crops: list[str] = Field(default_factory=list, max_length=20)
    land_size_acres: float | None = Field(default=None, ge=0, le=100000)
    irrigation_type: str = Field(default="", max_length=80)
    soil_type: str = Field(default="", max_length=80)
    farming_type: str = Field(default="", max_length=80)


class FarmerOut(BaseModel):
    id: str
    full_name: str
    language: str
    state: str
    district: str
    village: str
    crops: list[str]
    land_size_acres: float | None
    irrigation_type: str
    soil_type: str
    farming_type: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    conversation_id: str | None = None
    language: str | None = None
    location: str | None = None


class AgentSource(BaseModel):
    title: str = "Source"
    source: str = ""
    url: str | None = None
    type: str = "web"


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    language: str
    sources: list[AgentSource] = []
    used_tools: list[str] = []


class VoiceResponse(ChatResponse):
    transcript: str
    detected_language: str


class AdminUserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None
