"""商品接口封装。"""
from utils.request_util import RequestUtil


class GoodsApi:
    def list(self, keyword=None):
        params = {"keyword": keyword} if keyword is not None else None
        return RequestUtil.send("GET", "/api/goods", params=params)

    def detail(self, goods_id):
        return RequestUtil.send("GET", f"/api/goods/{goods_id}")

    def add(self, name, price, stock):
        return RequestUtil.send(
            "POST", "/api/goods/add",
            json={"name": name, "price": price, "stock": stock},
        )

    def update(self, goods_id, **fields):
        return RequestUtil.send("PUT", f"/api/goods/{goods_id}", json=fields)

    def delete(self, goods_id):
        return RequestUtil.send("DELETE", f"/api/goods/{goods_id}")
