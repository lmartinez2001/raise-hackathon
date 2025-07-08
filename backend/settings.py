from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str
    cookie_secure: bool
    credential_file: str
    session_duration: int
    redirect_uri: str
    scope: str
    secret_key: str
    target_drive_name: str
    hf_token: str
    frontend_url: str

    class Config:
        env_file = ".env"
