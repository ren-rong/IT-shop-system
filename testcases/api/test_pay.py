"""支付回调模块接口测试。"""
import pytest

from api.goods_api import GoodsApi
from api.order_api import OrderApi
from api.pay_api import PayApi


def get_goods_id(name):
    for g in GoodsApi().list().json()["data"]:
        if g["name"] == name:
            return g["id"]
    raise AssertionError(f"种子商品不存在: {name}")


def create_pending_order(qty=1):
    gid = get_goods_id("USB-C数据线")
    order_no = OrderApi().add(gid, qty).json()["data"]["order_no"]
    total = OrderApi().detail(order_no).json()["data"]["total_amount"]
    return order_no, total


class TestPay:
    @pytest.mark.smoke
    def test_pay_callback_success(self, admin_token, db):
        order_no, total = create_pending_order()
        resp = PayApi().callback(order_no, total, "success", "TRADE" + order_no)
        body = resp.json()
        assert resp.status_code == 200
        assert body["code"] == 200
        assert body["data"]["status"] == "PAID"
        # 数据库：订单状态已更新为 PAID
        assert db.query_one(
            "SELECT status FROM orders WHERE order_no=?", (order_no,)
        )["status"] == "PAID"

    def test_pay_creates_pay_record(self, admin_token, db):
        order_no, total = create_pending_order()
        trade = "TRADE" + order_no
        PayApi().callback(order_no, total, "success", trade)
        row = db.query_one(
            "SELECT * FROM pay_records WHERE order_no=?", (order_no,)
        )
        assert row is not None
        assert row["trade_no"] == trade
        assert row["status"] == "success"

    def test_paid_order_amount_correct(self, admin_token, db):
        order_no, total = create_pending_order(2)
        PayApi().callback(order_no, total, "success", "TRADE" + order_no)
        row = db.query_one(
            "SELECT amount FROM pay_records WHERE order_no=?", (order_no,)
        )
        assert abs(float(row["amount"]) - float(total)) < 0.01

    def test_pay_order_not_found(self, admin_token):
        resp = PayApi().callback("NO_NOT_EXIST_000", 1.0, "success", "T1")
        assert resp.status_code == 404
        assert resp.json()["code"] == 404
        assert "订单不存在" in resp.json()["msg"]

    def test_pay_amount_mismatch(self, admin_token, db):
        order_no, total = create_pending_order()
        body = PayApi().callback(order_no, 0.01, "success", "T_BAD").json()
        assert body["code"] == 400
        assert "支付金额与订单金额不一致" in body["msg"]
        # 订单仍待支付，且未生成支付记录
        assert db.query_one(
            "SELECT status FROM orders WHERE order_no=?", (order_no,)
        )["status"] == "PENDING"
        assert db.count(
            "SELECT COUNT(*) FROM pay_records WHERE order_no=?", (order_no,)
        ) == 0

    def test_duplicate_pay_callback(self, admin_token, db):
        order_no, total = create_pending_order()
        PayApi().callback(order_no, total, "success", "TRADE" + order_no)
        body = PayApi().callback(order_no, total, "success", "TRADE" + order_no).json()
        assert body["code"] == 400
        assert "请勿重复回调" in body["msg"]
        assert db.count(
            "SELECT COUNT(*) FROM pay_records WHERE order_no=?", (order_no,)
        ) == 1

    def test_pay_status_failed(self, admin_token, db):
        order_no, total = create_pending_order()
        body = PayApi().callback(order_no, total, "failed", "TRADE" + order_no).json()
        assert body["code"] == 400
        assert "支付失败" in body["msg"]
        assert db.query_one(
            "SELECT status FROM orders WHERE order_no=?", (order_no,)
        )["status"] == "PENDING"
