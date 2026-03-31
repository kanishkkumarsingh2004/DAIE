"""
In-house environment variable handling
Replaces python-dotenv dependency
"""

import os
from typing import Optional


def load_dotenv(dotenv_path: Optional[str] = None) -> None:
    """
    Load environment variables from a .env file into os.environ

    Args:
        dotenv_path: Path to .env file (default: '.env' in current directory)
    """
    if dotenv_path is None:
        dotenv_path = os.path.join(os.getcwd(), ".env")

    if not os.path.exists(dotenv_path):
        return

    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

                    # Set environment variable if not already set (unless we want to overwrite)
                    # Standard dotenv behavior is to NOT overwrite existing env vars
                    if key not in os.environ:
                        os.environ[key] = value
    except Exception as e:
        # Silently fail like python-dotenv often does, or log it
        pass
