"""订单管理页面 PO。"""
from pages.base_page import BasePage
from utils.config_loader import base_url


class OrderPage(BasePage):
    GOODS_ID = "#order-goods-id"
    QTY = "#order-quantity"
    CREATE_BTN = "#create-order-btn"
    MSG = "#order-msg"
    LIST = "#order-list"

    def goto_page(self):
        self.goto(base_url() + "/static/orders.html")
        self.wait_visible(self.CREATE_BTN)

    def create_order(self, goods_id, quantity):
        self.fill(self.GOODS_ID, goods_id)
        self.fill(self.QTY, quantity)
        self.click(self.CREATE_BTN)

    def get_msg(self):
        return (self.text(self.MSG) or "").strip()

    def row_exists(self, text):
        return self.page.locator(f"{self.LIST} tr", has_text=text).count() > 0
