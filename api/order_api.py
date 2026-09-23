"""订单接口封装。"""
from utils.request_util import RequestUtil


class OrderApi:
    def add(self, goods_id, quantity):
        return RequestUtil.send(
            "POST", "/api/orders/add",
            json={"goods_id": goods_id, "quantity": quantity},
        )

    def list(self):
        return RequestUtil.send("GET", "/api/orders")

    def detail(self, order_no):
        return RequestUtil.send("GET", f"/api/orders/{order_no}")

    def cancel(self, order_no):
        return RequestUtil.send("POST", f"/api/orders/{order_no}/cancel")
