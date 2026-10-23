from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="maria.gonzalez@email.com")
    password: str = Field(..., example="123456")


class LoginResponse(BaseModel):
    mensaje: str
    id_cliente: int
    nombre_cliente: str
    email: str
    token_sesion: str