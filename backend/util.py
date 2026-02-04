import re
from urllib.parse import unquote

def ck_str_to_dict(ck_str: str) -> dict:
    cookies_pattern = re.compile(r'(\w+)=([^;]+)(?:;|$)')
    return {key: unquote(value) for key, value in cookies_pattern.findall(ck_str)}

def mask_string(s: str, visible_start=2, visible_end=2) -> str:
    """
    Masks the middle part of a string with asterisks.
    Example: "123456789" -> "12*****89"
    """
    if not s:
        return ""
    if len(s) <= visible_start + visible_end:
        return "*" * len(s)
    return s[:visible_start] + "*" * 5 + s[-visible_end:]
