"""用户管理页面 PO。"""
from pages.base_page import BasePage
from utils.config_loader import base_url


class UserPage(BasePage):
    USERNAME = "#new-username"
    PASSWORD = "#new-password"
    PHONE = "#new-phone"
    ADD_BTN = "#add-user-btn"
    MSG = "#user-msg"
    LIST = "#user-list"

    def goto_page(self):
        self.goto(base_url() + "/static/users.html")
        self.wait_visible(self.ADD_BTN)

    def add_user(self, username, password, phone=""):
        self.fill(self.USERNAME, username)
        self.fill(self.PASSWORD, password)
        self.fill(self.PHONE, phone)
        self.click(self.ADD_BTN)

    def get_msg(self):
        return (self.text(self.MSG) or "").strip()

    def row_exists(self, name):
        return self.page.locator(f"{self.LIST} tr", has_text=name).count() > 0
