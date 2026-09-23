"""登录接口封装。"""
from utils.request_util import RequestUtil


class LoginApi:
    def login(self, username, password):
        return RequestUtil.send(
            "POST", "/api/login",
            json={"username": username, "password": password},
        )
