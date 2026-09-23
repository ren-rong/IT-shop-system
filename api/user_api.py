"""用户接口封装。"""
from utils.request_util import RequestUtil


class UserApi:
    def info(self):
        return RequestUtil.send("GET", "/api/users/info")

    def list(self, keyword=None):
        params = {"keyword": keyword} if keyword is not None else None
        return RequestUtil.send("GET", "/api/users", params=params)

    def add(self, username, password, phone=None):
        return RequestUtil.send(
            "POST", "/api/users/add",
            json={"username": username, "password": password, "phone": phone},
        )

    def detail(self, user_id):
        return RequestUtil.send("GET", f"/api/users/{user_id}")
