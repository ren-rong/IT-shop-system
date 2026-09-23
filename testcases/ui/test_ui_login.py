"""WebUI - 登录页面测试。"""
import pytest

from pages.login_page import LoginPage


class TestUILogin:
    @pytest.mark.smoke
    def test_ui_login_success(self, page, test_environment):
        lp = LoginPage(page)
        lp.goto_login()
        lp.login("testadmin", "123456")
        lp.wait_until_logged_in()
        # 登录后进入商品页，核心元素可见
        assert page.locator("#add-goods-btn").is_visible()
        # 等待列表异步加载完成
        page.wait_for_function(
            "document.querySelectorAll('#goods-list tr').length >= 4"
        )
        assert page.locator("#goods-list tr").count() >= 4

    def test_ui_login_welcome_title_visible(self, page, test_environment):
        lp = LoginPage(page)
        lp.goto_login()
        assert lp.is_visible(lp.WELCOME)
        assert "电商后台管理系统" in lp.text(lp.WELCOME)

    def test_ui_login_wrong_password(self, page, test_environment):
        lp = LoginPage(page)
        lp.goto_login()
        lp.login("testadmin", "wrong_password")
        # 仍停留在登录页并展示错误提示
        assert "用户名或密码错误" in lp.get_message()
        assert page.locator("#login-btn").is_visible()
