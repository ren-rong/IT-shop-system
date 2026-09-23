"""支付回调接口封装。"""
from utils.request_util import RequestUtil


class PayApi:
    def callback(self, order_no, amount, pay_status="success", trade_no=None):
        return RequestUtil.send(
            "POST", "/api/pay/callback",
            json={
                "order_no": order_no,
                "amount": amount,
                "pay_status": pay_status,
                "trade_no": trade_no,
            },
        )
