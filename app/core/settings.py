from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")

    APP_NAME: str = "HMS"
    API_PREFIX: str = "/api/v1"

    # Example: mysql+pymysql://user:password@localhost:3306/hms
    # DATABASE_URL: str = "mysql+pymysql://root:root@127.0.0.1:3306/hms2"
    # DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/hms_new"DATABASE

    ASYNC_DATABASE_URL: str = "mysql+aiomysql://root:OHMYFRIEND%40123@localhost:3306/hms_new"
    SYNC_DATABASE_URL: str = "mysql+pymysql://root:OHMYFRIEND%40123@localhost:3306/hms_new"

    JWT_SECRET: str = "change-this-in-env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    APPT_EMERGENCY_SURCHARGE_PERCENT: int = 25
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_BUCKET_NAME: Optional[str] = None
    S3_FOLDER: str = "invoices"
    BASE_URL: Optional[str] = None

settings = Settings()

# pathology
# load_dotenv(os.path.join(os.getcwd(),"app\.env"))
#
# SECRET_KEY = base64.urlsafe_b64encode(os.urandom(50)).decode()
#
# class Settings(BaseSettings):
#
#
#     APP_NAME: str = "Pathology Lab API"
#     ENV: str = "dev"
#     DATABASE_URL: str
#     JWT_SECRET:  str = SECRET_KEY
#     JWT_ALGO: str
#     ACCESS_TOKEN_EXPIRE_MINUTES: int
#     INSTALL_TOKEN: str
#     SUPERADMIN_LIMIT: int
#     ADMIN_LIMIT: int
#     TECHNICIAN_LIMIT: int
#     RECEPTIONIST_LIMIT: int
#     PUBLIC_BASE_URL: str
#     AWS_ACCESS_KEY_ID: str
#     AWS_SECRET_ACCESS_KEY: str
#     AWS_REGION: str
#     S3_BUCKET: str
#     S3_REPORT_PREFIX: str = "reports"
#     S3_INVOICE_PREFIX: str = "invoices"
#     REPORT_URL_EXPIRES: int
#     S3_SIGNATURE_PREFIX: str
#     SIGNATURE_URL_EXPIRES: int
#
#
#     class Config:
#         env_file = ".env"
#
# settings = Settings()
#
