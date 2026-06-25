import os
import shutil
import uuid
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_VIDEO_BYTES = 250 * 1024 * 1024
MAX_IMAGE_EDGE = 2048


class MediaStorageError(ValueError):
    pass


def _source_file(path):
    source = Path(str(path or "")).expanduser()
    if not source.is_file():
        raise MediaStorageError("선택한 파일을 찾을 수 없어요.")
    return source


def _validate_extension(source, allowed, label):
    extension = source.suffix.lower()
    if extension not in allowed:
        allowed_text = ", ".join(sorted(ext.lstrip(".").upper() for ext in allowed))
        raise MediaStorageError(f"{label}은 {allowed_text} 형식만 등록할 수 있어요.")
    return extension


def _validate_size(source, maximum, label):
    size = source.stat().st_size
    if size <= 0:
        raise MediaStorageError(f"비어 있는 {label} 파일은 등록할 수 없어요.")
    if size > maximum:
        limit_mb = maximum // (1024 * 1024)
        raise MediaStorageError(f"{label} 파일은 {limit_mb}MB 이하만 등록할 수 있어요.")
    return size


def validate_image_file(path):
    source = _source_file(path)
    _validate_extension(source, IMAGE_EXTENSIONS, "사진")
    size = _validate_size(source, MAX_IMAGE_BYTES, "사진")
    try:
        with Image.open(source) as image:
            image.verify()
        with Image.open(source) as image:
            width, height = image.size
    except (OSError, UnidentifiedImageError) as error:
        raise MediaStorageError("손상되었거나 지원하지 않는 사진 파일이에요.") from error
    return {
        "sourcePath": str(source.resolve()),
        "name": source.name,
        "size": size,
        "width": width,
        "height": height,
    }


def validate_video_file(path):
    source = _source_file(path)
    extension = _validate_extension(source, VIDEO_EXTENSIONS, "영상")
    size = _validate_size(source, MAX_VIDEO_BYTES, "영상")
    return {
        "sourcePath": str(source.resolve()),
        "name": source.name,
        "size": size,
        "extension": extension,
    }


def _media_subdirectory(media_root, user_id, kind):
    safe_user_id = str(user_id or "local_user").replace(os.sep, "_")
    directory = Path(media_root).expanduser() / safe_user_id / kind
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def store_image(path, media_root, user_id=None):
    metadata = validate_image_file(path)
    source = Path(metadata["sourcePath"])
    directory = _media_subdirectory(media_root, user_id, "images")

    try:
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original)
            image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE), Image.Resampling.LANCZOS)
            has_alpha = image.mode in {"RGBA", "LA"} or (
                image.mode == "P" and "transparency" in image.info
            )
            if has_alpha:
                output_path = directory / f"{uuid.uuid4().hex}.webp"
                image.convert("RGBA").save(output_path, "WEBP", quality=85, method=6)
                output_format = "webp"
            else:
                output_path = directory / f"{uuid.uuid4().hex}.jpg"
                image.convert("RGB").save(
                    output_path,
                    "JPEG",
                    quality=85,
                    optimize=True,
                    progressive=True,
                )
                output_format = "jpeg"
    except (OSError, UnidentifiedImageError) as error:
        raise MediaStorageError("사진을 압축해 저장하지 못했어요.") from error

    return {
        "path": str(output_path.resolve()),
        "name": source.name,
        "size": output_path.stat().st_size,
        "width": image.width,
        "height": image.height,
        "format": output_format,
    }


def store_images(paths, media_root, user_id=None, limit=10):
    unique_paths = []
    for path in paths or []:
        normalized = str(path or "")
        if normalized and normalized not in unique_paths:
            unique_paths.append(normalized)
    if len(unique_paths) > limit:
        raise MediaStorageError(f"사진은 최대 {limit}장까지 등록할 수 있어요.")

    stored = []
    try:
        for path in unique_paths:
            stored.append(store_image(path, media_root, user_id))
    except Exception:
        for item in stored:
            remove_media_file(item.get("path"), media_root)
        raise
    return stored


def store_video(path, media_root, user_id=None):
    metadata = validate_video_file(path)
    source = Path(metadata["sourcePath"])
    directory = _media_subdirectory(media_root, user_id, "videos")
    output_path = directory / f"{uuid.uuid4().hex}{metadata['extension']}"
    try:
        shutil.copy2(source, output_path)
    except OSError as error:
        raise MediaStorageError("영상을 앱 저장소로 복사하지 못했어요.") from error
    return {
        "path": str(output_path.resolve()),
        "name": source.name,
        "size": output_path.stat().st_size,
        "format": metadata["extension"].lstrip("."),
    }


def remove_media_file(path, media_root):
    if not path:
        return False
    target = Path(str(path)).expanduser().resolve()
    root = Path(media_root).expanduser().resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return False
    try:
        if target.is_file():
            target.unlink()
        return True
    except OSError:
        return False


def delete_user_media(media_root, user_id):
    """Remove all locally stored uploads owned by one user."""
    root = Path(media_root).expanduser().resolve()
    user_directory = (root / str(user_id or "")).resolve()
    try:
        user_directory.relative_to(root)
    except ValueError:
        return False
    try:
        if user_directory.exists():
            shutil.rmtree(user_directory)
        return True
    except OSError:
        return False
