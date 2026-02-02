import re
from urllib.parse import unquote

def ck_str_to_dict(ck_str: str) -> dict:
    cookies_pattern = re.compile(r'(\w+)=([^;]+)(?:;|$)')
    return {key: unquote(value) for key, value in cookies_pattern.findall(ck_str)}