"""
Environment loader with fallback.
Loads environment variables from .env file using python-dotenv if available,
or fallback pure-Python parsing if dotenv is not installed.
"""

import os
from pathlib import Path


def load_env():
    """Load variables from .env file into os.environ safely."""
    # 1. Try python-dotenv first
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return
    except ImportError:
        pass

    # 2. Pure Python fallback parser for .env
    # Search common locations: current dir, parent dir, or project root
    candidates = [
        Path(".env"),
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path.cwd() / ".env",
    ]

    for env_path in candidates:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # Ignore comments and empty lines
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        # Only set if not already present in environment
                        if key and key not in os.environ:
                            os.environ[key] = val
                break
            except Exception:
                pass
