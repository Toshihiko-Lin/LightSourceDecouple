import os
import sys
from datetime import datetime

from .raw_convert import IMAGE_EXTENSIONS, RAW_EXTENSIONS, TIFF_EXTENSIONS


APP_NAME = "DecoupleTool"
CONFIG_FILENAME = "config.json"
CALIBRATION_MATRIX_FILENAME = "calibration_matrix.npy"


def get_app_config_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")

    config_dir = os.path.join(base, APP_NAME)
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_standard_config_dir():
    return get_app_config_dir()


def get_config_path():
    return os.path.join(get_app_config_dir(), CONFIG_FILENAME)


def get_standard_config_path():
    return get_config_path()


def get_calibration_matrix_path():
    return os.path.join(get_app_config_dir(), CALIBRATION_MATRIX_FILENAME)


def format_cache_timestamp(path=None):
    cache_path = path or get_calibration_matrix_path()
    if not os.path.exists(cache_path):
        return ""
    stat_result = os.stat(cache_path)
    timestamp = getattr(stat_result, "st_birthtime", stat_result.st_mtime)
    created_at = datetime.fromtimestamp(timestamp)
    return created_at.strftime("%Y-%m-%d %H:%M")


def format_cache_created_at(path=None):
    return format_cache_timestamp(path)


def format_cache_created_date(path=None):
    timestamp = format_cache_timestamp(path)
    if not timestamp:
        return ""
    return timestamp.split(" ", 1)[0]


def format_cache_placeholder(path=None):
    timestamp = format_cache_timestamp(path)
    if not timestamp:
        return ""
    return f"默认使用已有文件，创建于 {timestamp}"


def file_type_label(path):
    ext = os.path.splitext(os.fspath(path))[1].lower()
    if ext in TIFF_EXTENSIONS:
        return "TIFF"
    if ext in RAW_EXTENSIONS:
        return "RAW"
    return ext.lstrip(".").upper() or "FILE"


def validate_input_image_files(paths):
    selected = []
    for path in paths or []:
        if path is None:
            continue
        value = os.fspath(path).strip()
        if value:
            selected.append(value)

    if not selected:
        raise ValueError("请选择至少一个输入文件")

    unsupported = [
        path
        for path in selected
        if os.path.splitext(path)[1].lower() not in IMAGE_EXTENSIONS
    ]
    if unsupported:
        names = "、".join(os.path.basename(path) for path in unsupported)
        raise ValueError(f"输入文件仅支持 TIFF 或 RAW；不支持: {names}")

    missing = [path for path in selected if not os.path.isfile(path)]
    if missing:
        names = "、".join(os.path.basename(path) or path for path in missing)
        raise ValueError(f"找不到输入文件: {names}")

    return selected


def validate_rgb_calibration_files(paths):
    selected = []
    for path in paths or []:
        if path is None:
            continue
        value = os.fspath(path).strip()
        if value:
            selected.append(value)

    if len(selected) != 3:
        raise ValueError(
            "RGB 校正文件必须正好选择 3 个 TIFF 文件，或正好 3 个 RAW 文件；"
            f"当前选择 {len(selected)} 个"
        )

    unsupported = [
        path
        for path in selected
        if os.path.splitext(path)[1].lower() not in TIFF_EXTENSIONS | RAW_EXTENSIONS
    ]
    if unsupported:
        names = "、".join(os.path.basename(path) for path in unsupported)
        raw_suffixes = "、".join(sorted(RAW_EXTENSIONS))
        raise ValueError(
            "RGB 校正文件仅支持 TIFF (.tif/.tiff) 或 RAW "
            f"({raw_suffixes})；不支持: {names}"
        )

    missing = [path for path in selected if not os.path.isfile(path)]
    if missing:
        names = "、".join(os.path.basename(path) or path for path in missing)
        raise ValueError(f"找不到 RGB 校正文件: {names}")

    tiff_count = sum(
        1 for path in selected if os.path.splitext(path)[1].lower() in TIFF_EXTENSIONS
    )
    raw_count = sum(
        1 for path in selected if os.path.splitext(path)[1].lower() in RAW_EXTENSIONS
    )

    if tiff_count == 3 or raw_count == 3:
        return selected

    raise ValueError(
        "RGB 校正文件必须全部为 TIFF，或全部为 RAW，不能混合选择；"
        f"当前 TIFF {tiff_count} 个，RAW {raw_count} 个"
    )
