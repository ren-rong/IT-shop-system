"""商品管理页面 PO。"""
from pages.base_page import BasePage
from utils.config_loader import base_url


class GoodsPage(BasePage):
    NAME = "#goods-name"
    PRICE = "#goods-price"
    STOCK = "#goods-stock"
    ADD_BTN = "#add-goods-btn"
    MSG = "#goods-msg"
    LIST = "#goods-list"

    def goto_page(self):
        self.goto(base_url() + "/static/goods.html")
        self.wait_visible(self.ADD_BTN)

    def add_goods(self, name, price, stock):
        self.fill(self.NAME, name)
        self.fill(self.PRICE, price)
        self.fill(self.STOCK, stock)
        self.click(self.ADD_BTN)

    def get_msg(self):
        return (self.text(self.MSG) or "").strip()

    def row_exists(self, name):
        return self.page.locator(f"{self.LIST} tr", has_text=name).count() > 0
