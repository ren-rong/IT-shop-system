"""登录模块接口测试：HTTP 状态 / 业务码与关键字段 / 数据库 三层断言。"""
import pytest
import requests

from api.login_api import LoginApi
from api.user_api import UserApi
from utils.config_loader import base_url

# 参数化：正常 3 + 异常 2
LOGIN_CASES = [
    # (用例名, 用户名, 密码, 期望业务码, 期望提示, 是否成功)
    ("正确账号admin", "admin", "123456", 200, "success", True),
    ("正确账号testadmin", "testadmin", "123456", 200, "success", True),
    ("正确账号buyer", "buyer", "123456", 200, "success", True),
    ("密码错误", "admin", "wrong_pwd", 400, "用户名或密码错误", False),
    ("用户名为空", "", "123456", 400, "用户名和密码不能为空", False),
]


class TestLogin:
    @pytest.mark.smoke
    @pytest.mark.parametrize("case", LOGIN_CASES,
                             ids=[c[0] for c in LOGIN_CASES])
    def test_login_param(self, case, db):
        name, username, password, expect_code, expect_msg, success = case
        resp = LoginApi().login(username, password)
        body = resp.json()

        # 第一层：HTTP 状态码
        assert resp.status_code == 200
        # 第二层：业务码 + 提示信息
        assert body["code"] == expect_code
        assert expect_msg in body["msg"]
        if success:
            # 第三层：数据库用户真实存在
            row = db.query_one("SELECT * FROM users WHERE username=?", (username,))
            assert row is not None
            # 第二层补充：成功返回 token
            assert body["data"]["token"]

    @pytest.mark.smoke
    def test_login_returns_token(self):
        body = LoginApi().login("testadmin", "123456").json()
        assert body["code"] == 200
        assert isinstance(body["data"]["token"], str) and body["data"]["token"]

    def test_login_returns_username(self):
        body = LoginApi().login("testadmin", "123456").json()
        assert body["data"]["username"] == "testadmin"

    def test_login_returns_role(self):
        body = LoginApi().login("admin", "123456").json()
        assert body["data"]["role"] == "admin"

    def test_login_msg_is_success(self):
        body = LoginApi().login("buyer", "123456").json()
        assert body["msg"] == "success"

    def test_repeat_login_ok(self):
        api = LoginApi()
        assert api.login("testadmin", "123456").json()["code"] == 200
        assert api.login("testadmin", "123456").json()["code"] == 200

    @pytest.mark.smoke
    def test_token_can_access_protected_api(self, admin_token):
        resp = UserApi().info()
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["username"] == "testadmin"

    def test_protected_api_without_token(self):
        # 原生请求，不携带 Token
        resp = requests.get(base_url() + "/api/users/info")
        assert resp.status_code == 401
        assert resp.json()["detail"]
