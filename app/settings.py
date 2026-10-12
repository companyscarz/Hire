import os
import secrets

from dotenv import load_dotenv

load_dotenv()

from users.models.models_company import COmpany
from users.models.models_applicant import APplicant
from users.models.models_advertisement import ADvertisement
from admin.models.models_staff import STaff
from users.models.models_block import BLock
from users.models.models_about import ABout


def _as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    # Production deployments must supply a stable, secret value through the
    # environment. The random fallback is only for local development.
    ENV = os.getenv("APP_ENV", "development").strip().lower()
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if ENV == "production":
            raise RuntimeError("SECRET_KEY must be set when APP_ENV=production")
        SECRET_KEY = secrets.token_urlsafe(32)

    DEBUG = _as_bool("FLASK_DEBUG", default=(ENV != "production"))

    # Legacy configuration values are now environment-based. Replace/rotate
    # any credentials that were previously committed to Git.
    CODE_1 = os.getenv("CODE_1", "")
    CODE_2 = os.getenv("CODE_2", "")
    RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_PUBLIC_KEY", "")
    RECAPTCHA_PRIVATE_KEY = os.getenv("RECAPTCHA_PRIVATE_KEY", "")
    Openai = os.getenv("OPENAI_API_KEY", "")
    mapbox = os.getenv("MAPBOX_PUBLIC_TOKEN", "")

    # Kept for the legacy development entry point; production serving should
    # be performed by the deployment's WSGI server.
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8080"))

    # Legacy Hire data-model objects remain temporarily for compatibility.
    # They will be removed when the old job-board application is replaced.
    block = BLock("0", "1")
    suggestions = ABout("0", "1")
    advertisements = ADvertisement("0", "1", "2", "3", "4", "5", "6", "7", "8")
    applications = APplicant(
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"
    )
    opportunities = COmpany(
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11",
        "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23"
    )
    members = STaff("local", "local@example.invalid", "0", "0", "local.txt", "text/plain", "unspecified", "", "0")
