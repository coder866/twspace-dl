# src/xspace_dl/config.py
import os
from dotenv import load_dotenv
from .cookie_manager import CookieManager
from .logger import setup_logger

logger = setup_logger(__name__)


class Config:
    def __init__(self):
        load_dotenv()

        self.auth_token = None
        self.ct0 = None
        self.mode = "GUEST"

        self._load_configuration()

    def _load_configuration(self):
        """Determines the authentication strategy."""

        # 1. Strategy: Environment Variables (Manual Override)
        env_auth = os.getenv("X_AUTH_TOKEN")
        env_ct0 = os.getenv("X_CT0")

        if env_auth and env_ct0:
            self.auth_token = env_auth
            self.ct0 = env_ct0
            self.mode = "USER (Environment)"
            logger.info("Configuration loaded from .env file.")
            return

        # 2. Strategy: Automatic Discovery (Chrome / cookies.txt)
        logger.info("No .env credentials. Starting auto-discovery...")
        discovered = CookieManager.get_auth_cookies()

        if discovered:
            self.auth_token = discovered["auth_token"]
            self.ct0 = discovered["ct0"]
            self.mode = "USER (Auto-Discovered)"
        else:
            self.mode = "GUEST"
            logger.warning(
                "Falling back to Guest Mode. Private/NSFW Spaces will not be accessible."
            )

    @property
    def is_user_authenticated(self):
        return "USER" in self.mode
