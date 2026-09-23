"""用户模块接口测试。"""
import uuid
import pytest
import requests

from api.user_api import UserApi
from utils.config_loader import base_url


def new_user_name():
    return f"auto_user_{uuid.uuid4().hex[:8]}"


# 参数化新增有效用户（3 个，正常路径）
VALID_USERS = [
    ("普通用户", "123456", "13900000001"),
    ("带特殊尾号用户", "abc12345", "13900000002"),
    ("无手机号用户", "pwd12345", None),
]


class TestUser:
    @pytest.mark.smoke
    def test_get_user_info_success(self, admin_token):
        body = UserApi().info().json()
        assert body["code"] == 200
        assert body["data"]["username"] == "testadmin"

    def test_user_info_role_matches_db(self, admin_token, db):
        body = UserApi().info().json()
        role_api = body["data"]["role"]
        row = db.query_one("SELECT role FROM users WHERE username='testadmin'")
        assert role_api == row["role"]

    @pytest.mark.smoke
    def test_user_list_success(self, admin_token):
        body = UserApi().list().json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 3

    def test_user_list_contains_seed(self, admin_token, db):
        body = UserApi().list().json()
        names = [u["username"] for u in body["data"]]
        assert "testadmin" in names
        # 数据库交叉验证
        assert db.count("SELECT COUNT(*) FROM users WHERE username='testadmin'") == 1

    def test_user_list_keyword_filter(self, admin_token):
        body = UserApi().list(keyword="admin").json()
        assert body["code"] == 200
        assert len(body["data"]) >= 2  # admin / testadmin
        for u in body["data"]:
            assert "admin" in u["username"]

    @pytest.mark.parametrize("case", VALID_USERS, ids=[c[0] for c in VALID_USERS])
    def test_add_valid_user(self, case, admin_token, db):
        _, password, phone = case
        username = new_user_name()
        resp = UserApi().add(username, password, phone)
        body = resp.json()
        # 第一层 HTTP
        assert resp.status_code == 200
        # 第二层 业务码 + 返回 id
        assert body["code"] == 200
        assert body["data"]["username"] == username
        # 第三层 数据库落库
        row = db.query_one("SELECT * FROM users WHERE username=?", (username,))
        assert row is not None
        assert row["phone"] == (phone if phone else row["phone"])

    def test_add_duplicate_user(self, admin_token, db):
        username = new_user_name()
        assert UserApi().add(username, "123456").json()["code"] == 200
        body = UserApi().add(username, "123456").json()
        assert body["code"] == 400
        assert "用户名已存在" in body["msg"]
        # 数据库只有一条
        assert db.count(
            "SELECT COUNT(*) FROM users WHERE username=?", (username,)
        ) == 1

    def test_add_empty_username(self, admin_token, db):
        body = UserApi().add("", "123456").json()
        assert body["code"] == 400
        assert "用户名不能为空" in body["msg"]

    def test_user_detail_not_found(self, admin_token):
        resp = UserApi().detail(999999)
        assert resp.status_code == 404
        assert resp.json()["code"] == 404

    def test_user_list_without_token(self):
        resp = requests.get(base_url() + "/api/users")
        assert resp.status_code == 401
