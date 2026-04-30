"""JSON-file credential storage in <project_root>/.credentials/.

One file per integration (e.g. slack.json, github.json). The directory
location comes from ConfigStore.project_root, which the host sets via
configure(project_root=...).
"""
from __future__ import annotations

import json
import os
import stat
from dataclasses import asdict, fields
from pathlib import Path
from typing import Optional, Type, TypeVar

from .config import ConfigStore
from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def _credentials_dir() -> Path:
    path = ConfigStore.project_root / ".credentials"
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, stat.S_IRWXU)
    except OSError:
        pass
    return path


def has_credential(filename: str) -> bool:
    return (_credentials_dir() / filename).exists()


def load_credential(filename: str, credential_cls: Type[T]) -> Optional[T]:
    path = _credentials_dir() / filename
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        valid = {fld.name for fld in fields(credential_cls)}
        return credential_cls(**{k: v for k, v in data.items() if k in valid})
    except Exception as e:
        logger.warning(f"Failed to load credential {filename}: {e}")
        return None


def save_credential(filename: str, credential) -> None:
    path = _credentials_dir() / filename
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(credential), f, indent=2, default=str)
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        logger.info(f"Saved credential: {filename}")
    except Exception as e:
        logger.error(f"Failed to save credential {filename}: {e}")


def remove_credential(filename: str) -> bool:
    path = _credentials_dir() / filename
    if path.exists():
        path.unlink()
        logger.info(f"Removed credential: {filename}")
        return True
    return False
