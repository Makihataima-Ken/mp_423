from __future__ import annotations

import uuid
from pathlib import Path


def ensure_temp_dir(temp_dir: Path) -> Path:
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def unique_file_path(temp_dir: Path, suffix: str) -> Path:
    return temp_dir / f"{uuid.uuid4().hex}{suffix}"


def cleanup_files(*paths: Path) -> None:
    for path in paths:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            # Best-effort cleanup only.
            continue
