"""WebUI - 商品管理页面测试。"""
import uuid
import pytest

from pages.goods_page import GoodsPage


def ui_goods_name():
    return f"auto_ui_goods_{uuid.uuid4().hex[:8]}"


class TestUIGoods:
    @pytest.mark.smoke
    def test_goods_list_loads(self, logged_page):
        gp = GoodsPage(logged_page)
        gp.goto_page()
        assert gp.row_count(gp.LIST) >= 4

    @pytest.mark.smoke
    def test_add_goods_success(self, logged_page, db):
        gp = GoodsPage(logged_page)
        gp.goto_page()
        name = ui_goods_name()
        gp.add_goods(name, 19.9, 20)
        # 第一层：页面操作成功提示
        assert "新增商品成功" in gp.get_msg()
        # 第二层：列表中出现该商品
        assert gp.row_exists(name)
        # 第三层：数据库已落库
        row = db.query_one("SELECT * FROM goods WHERE name=?", (name,))
        assert row is not None
        assert float(row["price"]) == 19.9

    def test_add_goods_shows_in_list(self, logged_page):
        gp = GoodsPage(logged_page)
        gp.goto_page()
        name = ui_goods_name()
        gp.add_goods(name, 8.8, 9)
        assert gp.row_exists(name)

    def test_add_goods_empty_name(self, logged_page):
        gp = GoodsPage(logged_page)
        gp.goto_page()
        gp.add_goods("", 10.0, 5)
        assert "商品名称不能为空" in gp.get_msg()
