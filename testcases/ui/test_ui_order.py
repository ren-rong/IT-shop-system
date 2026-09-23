"""WebUI - 订单管理页面测试。"""
import pytest

from api.goods_api import GoodsApi
from pages.order_page import OrderPage


def get_goods_id(name):
    for g in GoodsApi().list().json()["data"]:
        if g["name"] == name:
            return g["id"]
    raise AssertionError(f"种子商品不存在: {name}")


class TestUIOrder:
    def test_order_page_loads(self, logged_page):
        op = OrderPage(logged_page)
        op.goto_page()
        assert op.is_visible(op.CREATE_BTN)

    @pytest.mark.smoke
    def test_create_order_success(self, logged_page, db):
        op = OrderPage(logged_page)
        op.goto_page()
        gid = get_goods_id("无线鼠标")
        op.create_order(gid, 1)
        # 第一层：成功提示
        assert "下单成功" in op.get_msg()
        # 取列表第一行（最新倒序）订单号
        order_no = logged_page.locator("#order-list .order-no").first.text_content()
        # 第二层：列表出现该订单
        assert op.row_exists("无线鼠标")
        # 第三层：数据库订单存在且为待支付
        row = db.query_one("SELECT * FROM orders WHERE order_no=?", (order_no,))
        assert row is not None
        assert row["status"] == "PENDING"

    def test_order_created_shows_in_list(self, logged_page):
        op = OrderPage(logged_page)
        op.goto_page()
        gid = get_goods_id("USB-C数据线")
        op.create_order(gid, 2)
        assert op.row_exists("USB-C数据线")

    def test_create_order_insufficient_stock(self, logged_page):
        op = OrderPage(logged_page)
        op.goto_page()
        gid = get_goods_id("4K显示器")
        op.create_order(gid, 99999)
        assert "库存不足" in op.get_msg()
