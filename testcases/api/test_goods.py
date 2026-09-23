"""商品模块接口测试。"""
import uuid
import pytest

from api.goods_api import GoodsApi


def new_goods_name():
    return f"auto_goods_{uuid.uuid4().hex[:8]}"


VALID_GOODS = [
    ("常规商品", 59.9, 100),
    ("整数价格商品", 100.0, 50),
    ("高库存商品", 1.5, 9999),
]


class TestGoods:
    @pytest.mark.smoke
    def test_goods_list_success(self, admin_token):
        body = GoodsApi().list().json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 4

    def test_goods_list_contains_seed(self, admin_token, db):
        body = GoodsApi().list().json()
        names = [g["name"] for g in body["data"]]
        assert "机械键盘" in names
        assert db.count("SELECT COUNT(*) FROM goods WHERE name='机械键盘'") == 1

    def test_goods_list_keyword_filter(self, admin_token):
        body = GoodsApi().list(keyword="鼠标").json()
        assert body["code"] == 200
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == "无线鼠标"

    def test_goods_detail_success(self, admin_token):
        gid = GoodsApi().list().json()["data"][0]["id"]
        body = GoodsApi().detail(gid).json()
        assert body["code"] == 200
        assert body["data"]["id"] == gid
        assert body["data"]["name"]

    @pytest.mark.parametrize("case", VALID_GOODS, ids=[c[0] for c in VALID_GOODS])
    def test_add_valid_goods(self, case, admin_token, db):
        _, price, stock = case
        name = new_goods_name()
        resp = GoodsApi().add(name, price, stock)
        body = resp.json()
        assert resp.status_code == 200
        assert body["code"] == 200
        assert body["data"]["id"]
        # 数据库校验
        row = db.query_one("SELECT * FROM goods WHERE name=?", (name,))
        assert row is not None
        assert float(row["price"]) == price
        assert row["stock"] == stock

    def test_update_goods_price(self, admin_token, db):
        name = new_goods_name()
        gid = GoodsApi().add(name, 50.0, 10).json()["data"]["id"]
        body = GoodsApi().update(gid, price=66.6).json()
        assert body["code"] == 200
        assert float(body["data"]["price"]) == 66.6
        row = db.query_one("SELECT price FROM goods WHERE id=?", (gid,))
        assert abs(float(row["price"]) - 66.6) < 0.001

    def test_update_goods_stock(self, admin_token, db):
        name = new_goods_name()
        gid = GoodsApi().add(name, 50.0, 10).json()["data"]["id"]
        body = GoodsApi().update(gid, stock=88).json()
        assert body["code"] == 200
        assert body["data"]["stock"] == 88
        assert db.query_one("SELECT stock FROM goods WHERE id=?", (gid,))["stock"] == 88

    @pytest.mark.smoke
    def test_delete_goods(self, admin_token, db):
        name = new_goods_name()
        gid = GoodsApi().add(name, 50.0, 10).json()["data"]["id"]
        resp = GoodsApi().delete(gid)
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert db.query_one("SELECT * FROM goods WHERE id=?", (gid,)) is None

    def test_add_empty_name(self, admin_token, db):
        body = GoodsApi().add("", 10.0, 5).json()
        assert body["code"] == 400
        assert "商品名称不能为空" in body["msg"]
        assert db.count("SELECT COUNT(*) FROM goods WHERE name=''") == 0

    def test_add_zero_price(self, admin_token):
        body = GoodsApi().add(new_goods_name(), 0, 5).json()
        assert body["code"] == 400
        assert "商品价格必须大于0" in body["msg"]

    def test_add_duplicate_name(self, admin_token, db):
        body = GoodsApi().add("机械键盘", 199.0, 10).json()
        assert body["code"] == 400
        assert "商品名称已存在" in body["msg"]
        assert db.count("SELECT COUNT(*) FROM goods WHERE name='机械键盘'") == 1

    def test_goods_detail_not_found(self, admin_token):
        resp = GoodsApi().detail(999999)
        assert resp.status_code == 404
        assert resp.json()["code"] == 404
