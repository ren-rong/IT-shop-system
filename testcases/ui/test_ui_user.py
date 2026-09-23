"""WebUI - 用户管理页面测试。"""
import uuid
import pytest

from pages.user_page import UserPage


def ui_user_name():
    return f"auto_ui_user_{uuid.uuid4().hex[:8]}"


class TestUIUser:
    @pytest.mark.smoke
    def test_user_list_loads(self, logged_page):
        up = UserPage(logged_page)
        up.goto_page()
        up.wait_row_count_atleast(up.LIST, 3)
        assert up.row_count(up.LIST) >= 3

    @pytest.mark.smoke
    def test_add_user_success(self, logged_page, db):
        up = UserPage(logged_page)
        up.goto_page()
        name = ui_user_name()
        up.add_user(name, "123456", "13700000001")
        # 第一层：成功提示
        assert "新增用户成功" in up.get_msg()
        # 第二层：列表出现
        assert up.row_exists(name)
        # 第三层：数据库落库
        assert db.query_one("SELECT * FROM users WHERE username=?", (name,))

    def test_add_user_duplicate(self, logged_page):
        up = UserPage(logged_page)
        up.goto_page()
        up.add_user("testadmin", "123456", "")
        assert "用户名已存在" in up.get_msg()
