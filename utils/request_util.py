"""
请求封装：
- 统一拼接 base_url、统一 Content-Type
- 自动携带登录 Token（鉴权）
- 完整记录请求方法/地址/入参与响应状态/响应体，便于失败排查
"""
import requests

from utils.config_loader import base_url
from utils.log_util import logger


class RequestUtil:
    _token = ""

    @classmethod
    def set_token(cls, token):
        cls._token = token

    @classmethod
    def send(cls, method, path, **kwargs):
        url = base_url() + path
        headers = dict(kwargs.pop("headers", {}))
        headers.setdefault("Content-Type", "application/json")
        # 鉴权：自动注入 Bearer Token
        if cls._token:
            headers.setdefault("Authorization", f"Bearer {cls._token}")

        logger.info(
            f"--> {method.upper()} {url} | json={kwargs.get('json')} "
            f"| params={kwargs.get('params')}"
        )
        resp = requests.request(method, url, headers=headers, timeout=15, **kwargs)
        logger.info(f"<-- HTTP {resp.status_code} | {resp.text}")
        return resp
