"""計算結果を S3 に公開する。"""

from __future__ import annotations

from pathlib import Path


def content_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "application/json; charset=utf-8"
    if suffix == ".csv":
        return "text/csv; charset=utf-8"
    return "application/octet-stream"


def cache_control_for(path: Path) -> str:
    if path.name == "today_games.json":
        return "public, max-age=60"
    return "public, max-age=300"


def object_key(prefix: str, name: str) -> str:
    trimmed = prefix.strip("/")
    return f"{trimmed}/{name}" if trimmed else name


def iter_public_files(output_dir: Path) -> list[Path]:
    if not output_dir.is_dir():
        return []
    return sorted(path for path in output_dir.iterdir() if path.is_file())


def upload_output_dir(bucket: str, prefix: str, output_dir: Path, client) -> list[str]:
    uploaded: list[str] = []
    for path in iter_public_files(output_dir):
        key = object_key(prefix, path.name)
        client.upload_file(
            str(path),
            bucket,
            key,
            ExtraArgs={
                "ContentType": content_type_for(path),
                "CacheControl": cache_control_for(path),
            },
        )
        uploaded.append(key)
    return uploaded
