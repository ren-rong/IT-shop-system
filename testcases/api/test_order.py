"""订单模块接口测试：下单、查询、取消，含库存变动数据库校验。"""
import pytest
import requests

from api.goods_api import GoodsApi
from api.order_api import OrderApi
from api.pay_api import PayApi
from utils.config_loader import base_url


def get_goods_id(name):
    for g in GoodsApi().list().json()["data"]:
        if g["name"] == name:
            return g["id"]
    raise AssertionError(f"种子商品不存在: {name}")


CREATE_CASES = [
    ("购买数量1", 1),
    ("购买数量2", 2),
]


class TestOrder:
    @pytest.mark.smoke
    @pytest.mark.parametrize("case", CREATE_CASES, ids=[c[0] for c in CREATE_CASES])
    def test_create_order_param(self, case, admin_token, db):
        _, qty = case
        gid = get_goods_id("机械键盘")
        resp = OrderApi().add(gid, qty)
        body = resp.json()
        # 第一层 HTTP
        assert resp.status_code == 200
        # 第二层 业务码 + 订单号/状态
        assert body["code"] == 200
        assert body["data"]["order_no"].startswith("NO")
        assert body["data"]["status"] == "PENDING"
        # 第三层 数据库订单落库
        row = db.query_one(
            "SELECT * FROM orders WHERE order_no=?", (body["data"]["order_no"],)
        )
        assert row is not None
        assert row["quantity"] == qty

    def test_create_order_deduct_stock(self, admin_token, db):
        gid = get_goods_id("机械键盘")
        before = db.query_one("SELECT stock FROM goods WHERE id=?", (gid,))["stock"]
        OrderApi().add(gid, 2)
        after = db.query_one("SELECT stock FROM goods WHERE id=?", (gid,))["stock"]
        assert before - after == 2

    def test_order_list_success(self, admin_token):
        body = OrderApi().list().json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)

    def test_order_detail_success(self, admin_token, db):
        gid = get_goods_id("无线鼠标")
        order_no = OrderApi().add(gid, 1).json()["data"]["order_no"]
        body = OrderApi().detail(order_no).json()
        assert body["code"] == 200
        assert body["data"]["order_no"] == order_no
        assert db.query_one("SELECT * FROM orders WHERE order_no=?", (order_no,))

    @pytest.mark.smoke
    def test_cancel_order_success(self, admin_token, db):
        gid = get_goods_id("无线鼠标")
        order_no = OrderApi().add(gid, 1).json()["data"]["order_no"]
        body = OrderApi().cancel(order_no).json()
        assert body["code"] == 200
        assert body["data"]["status"] == "CANCELLED"
        assert db.query_one(
            "SELECT status FROM orders WHERE order_no=?", (order_no,)
        )["status"] == "CANCELLED"

    def test_cancel_order_restore_stock(self, admin_token, db):
        gid = get_goods_id("机械键盘")
        before = db.query_one("SELECT stock FROM goods WHERE id=?", (gid,))["stock"]
        order_no = OrderApi().add(gid, 3).json()["data"]["order_no"]
        OrderApi().cancel(order_no)
        after = db.query_one("SELECT stock FROM goods WHERE id=?", (gid,))["stock"]
        assert after == before

    def test_order_goods_not_found(self, admin_token):
        resp = OrderApi().add(999999, 1)
        assert resp.status_code == 404
        assert resp.json()["code"] == 404
        assert "商品不存在" in resp.json()["msg"]

    def test_order_quantity_zero(self, admin_token):
        body = OrderApi().add(get_goods_id("机械键盘"), 0).json()
        assert body["code"] == 400
        assert "购买数量必须大于0" in body["msg"]

    def test_order_insufficient_stock(self, admin_token, db):
        gid = get_goods_id("4K显示器")
        body = OrderApi().add(gid, 99999).json()
        assert body["code"] == 400
        assert "库存不足" in body["msg"]
        # 失败不应产生订单、库存不变
        assert db.query_one(
            "SELECT stock FROM goods WHERE id=?", (gid,)
        )["stock"] == 50

    def test_cancel_paid_order(self, admin_token, db):
        gid = get_goods_id("机械键盘")
        order_no = OrderApi().add(gid, 1).json()["data"]["order_no"]
        total = OrderApi().detail(order_no).json()["data"]["total_amount"]
        PayApi().callback(order_no, total, "success", "T" + order_no)
        body = OrderApi().cancel(order_no).json()
        assert body["code"] == 400
        assert "订单已支付，无法取消" in body["msg"]
        assert db.query_one(
            "SELECT status FROM orders WHERE order_no=?", (order_no,)
        )["status"] == "PAID"

    def test_create_order_without_token(self):
        resp = requests.post(
            base_url() + "/api/orders/add",
            json={"goods_id": 1, "quantity": 1},
        )
        assert resp.status_code == 401
