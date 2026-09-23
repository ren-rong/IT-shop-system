"""登录页面 PO。"""
from pages.base_page import BasePage
from utils.config_loader import web_login_url


class LoginPage(BasePage):
    USERNAME = "#username"
    PASSWORD = "#password"
    LOGIN_BTN = "#login-btn"
    MESSAGE = "#message"
    WELCOME = "#welcome-title"

    def goto_login(self):
        self.goto(web_login_url())
        self.wait_visible(self.LOGIN_BTN)

    def login(self, username, password):
        self.fill(self.USERNAME, username)
        self.fill(self.PASSWORD, password)
        self.click(self.LOGIN_BTN)

    def get_message(self):
        return (self.text(self.MESSAGE) or "").strip()

    def wait_until_logged_in(self, timeout=10000):
        self.page.wait_for_url("**/goods.html", timeout=timeout)
