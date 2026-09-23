"""
电商后台 FastAPI 主应用
覆盖：登录鉴权、用户管理、商品管理、下单/取消、支付回调
同时托管 /static 下的前端页面，供 WebUI 自动化测试。
"""
import os
import random
import string
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, Query
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import database as db
from .auth import create_token, get_current_user
from .schemas import (
    LoginRequest, UserAddRequest, GoodsAddRequest, GoodsUpdateRequest,
    OrderCreateRequest, PayCallbackRequest,
)

app = FastAPI(title="电商后台测试系统", version="1.0.0")

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------- 统一响应 ----------------
def ok(data=None, msg="success"):
    return JSONResponse(status_code=200, content={"code": 200, "msg": msg, "data": data})


def fail(msg, code=400, http_status=200):
    return JSONResponse(status_code=http_status, content={"code": code, "msg": msg, "data": None})


def gen_order_no():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = "".join(random.choices(string.digits, k=6))
    return f"NO{ts}{rand}"


@app.on_event("startup")
def startup():
    db.init_db()


@app.get("/")
def index():
    return RedirectResponse(url="/static/login.html")


# ---------------- 登录 ----------------
@app.post("/api/login")
def login(req: LoginRequest):
    username = (req.username or "").strip()
    password = req.password or ""
    if not username or not password:
        return fail("用户名和密码不能为空")
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        if row is None or row["password"] != db.hash_password(password):
            return fail("用户名或密码错误")
        token = create_token(row["username"], row["role"])
        return ok({"token": token, "username": row["username"], "role": row["role"]})
    finally:
        conn.close()


# ---------------- 用户 ----------------
@app.get("/api/users/info")
def user_info(current=Depends(get_current_user)):
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT username, phone, role FROM users WHERE username=?",
            (current["username"],),
        ).fetchone()
        if row is None:
            return fail("用户不存在", code=404, http_status=404)
        return ok(dict(row))
    finally:
        conn.close()


@app.get("/api/users")
def user_list(keyword: Optional[str] = Query(None), current=Depends(get_current_user)):
    conn = db.get_conn()
    try:
        if keyword:
            rows = conn.execute(
                "SELECT id, username, phone, role, created_at FROM users "
                "WHERE username LIKE ? ORDER BY id",
                (f"%{keyword}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, username, phone, role, created_at FROM users ORDER BY id"
            ).fetchall()
        return ok([dict(r) for r in rows])
    finally:
        conn.close()


@app.post("/api/users/add")
def user_add(req: UserAddRequest, current=Depends(get_current_user)):
    username = (req.username or "").strip()
    password = req.password or ""
    if not username:
        return fail("用户名不能为空")
    if not password:
        return fail("密码不能为空")
    conn = db.get_conn()
    try:
        exists = conn.execute(
            "SELECT id FROM users WHERE username=?", (username,)
        ).fetchone()
        if exists:
            return fail("用户名已存在")
        cur = conn.execute(
            "INSERT INTO users(username,password,phone,role,created_at) VALUES(?,?,?,?,?)",
            (username, db.hash_password(password), req.phone, "user",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        return ok({"id": cur.lastrowid, "username": username})
    finally:
        conn.close()


@app.get("/api/users/{user_id}")
def user_detail(user_id: int, current=Depends(get_current_user)):
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT id, username, phone, role, created_at FROM users WHERE id=?",
            (user_id,),
        ).fetchone()
        if row is None:
            return fail("用户不存在", code=404, http_status=404)
        return ok(dict(row))
    finally:
        conn.close()


# ---------------- 商品 ----------------
@app.get("/api/goods")
def goods_list(keyword: Optional[str] = Query(None)):
    conn = db.get_conn()
    try:
        if keyword:
            rows = conn.execute(
                "SELECT * FROM goods WHERE name LIKE ? ORDER BY id", (f"%{keyword}%",)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM goods ORDER BY id").fetchall()
        return ok([dict(r) for r in rows])
    finally:
        conn.close()


@app.get("/api/goods/{gid}")
def goods_detail(gid: int):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT * FROM goods WHERE id=?", (gid,)).fetchone()
        if row is None:
            return fail("商品不存在", code=404, http_status=404)
        return ok(dict(row))
    finally:
        conn.close()


@app.post("/api/goods/add")
def goods_add(req: GoodsAddRequest, current=Depends(get_current_user)):
    name = (req.name or "").strip()
    if not name:
        return fail("商品名称不能为空")
    if req.price is None or req.price <= 0:
        return fail("商品价格必须大于0")
    if req.stock is None or req.stock < 0:
        return fail("商品库存不能为负数")
    conn = db.get_conn()
    try:
        exists = conn.execute("SELECT id FROM goods WHERE name=?", (name,)).fetchone()
        if exists:
            return fail("商品名称已存在")
        cur = conn.execute(
            "INSERT INTO goods(name,price,stock,created_at) VALUES(?,?,?,?)",
            (name, req.price, req.stock, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        return ok({"id": cur.lastrowid, "name": name, "price": req.price, "stock": req.stock})
    finally:
        conn.close()


@app.put("/api/goods/{gid}")
def goods_update(gid: int, req: GoodsUpdateRequest, current=Depends(get_current_user)):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT * FROM goods WHERE id=?", (gid,)).fetchone()
        if row is None:
            return fail("商品不存在", code=404, http_status=404)
        if req.price is not None and req.price <= 0:
            return fail("商品价格必须大于0")
        new_name = req.name if req.name is not None else row["name"]
        new_price = req.price if req.price is not None else row["price"]
        new_stock = req.stock if req.stock is not None else row["stock"]
        conn.execute(
            "UPDATE goods SET name=?, price=?, stock=? WHERE id=?",
            (new_name, new_price, new_stock, gid),
        )
        conn.commit()
        return ok({"id": gid, "name": new_name, "price": new_price, "stock": new_stock})
    finally:
        conn.close()


@app.delete("/api/goods/{gid}")
def goods_delete(gid: int, current=Depends(get_current_user)):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT id FROM goods WHERE id=?", (gid,)).fetchone()
        if row is None:
            return fail("商品不存在", code=404, http_status=404)
        conn.execute("DELETE FROM goods WHERE id=?", (gid,))
        conn.commit()
        return ok({"id": gid}, msg="删除成功")
    finally:
        conn.close()


# ---------------- 订单 ----------------
@app.post("/api/orders/add")
def order_add(req: OrderCreateRequest, current=Depends(get_current_user)):
    if req.quantity is None or req.quantity <= 0:
        return fail("购买数量必须大于0")
    conn = db.get_conn()
    try:
        goods = conn.execute(
            "SELECT * FROM goods WHERE id=?", (req.goods_id,)
        ).fetchone()
        if goods is None:
            return fail("商品不存在", code=404, http_status=404)
        if goods["stock"] < req.quantity:
            return fail("库存不足")
        total = round(goods["price"] * req.quantity, 2)
        order_no = gen_order_no()
        conn.execute(
            "UPDATE goods SET stock=? WHERE id=?",
            (goods["stock"] - req.quantity, goods["id"]),
        )
        cur = conn.execute(
            "INSERT INTO orders(order_no,username,goods_id,goods_name,quantity,"
            "total_amount,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (order_no, current["username"], goods["id"], goods["name"],
             req.quantity, total, db.ORDER_PENDING,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        return ok({"order_no": order_no, "total_amount": total, "status": db.ORDER_PENDING})
    finally:
        conn.close()


@app.get("/api/orders")
def order_list(current=Depends(get_current_user)):
    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM orders ORDER BY id DESC"
        ).fetchall()
        return ok([dict(r) for r in rows])
    finally:
        conn.close()


@app.get("/api/orders/{order_no}")
def order_detail(order_no: str, current=Depends(get_current_user)):
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM orders WHERE order_no=?", (order_no,)
        ).fetchone()
        if row is None:
            return fail("订单不存在", code=404, http_status=404)
        return ok(dict(row))
    finally:
        conn.close()


@app.post("/api/orders/{order_no}/cancel")
def order_cancel(order_no: str, current=Depends(get_current_user)):
    conn = db.get_conn()
    try:
        order = conn.execute(
            "SELECT * FROM orders WHERE order_no=?", (order_no,)
        ).fetchone()
        if order is None:
            return fail("订单不存在", code=404, http_status=404)
        if order["status"] == db.ORDER_PAID:
            return fail("订单已支付，无法取消")
        if order["status"] == db.ORDER_PENDING:
            conn.execute(
                "UPDATE goods SET stock=stock+? WHERE id=?",
                (order["quantity"], order["goods_id"]),
            )
        conn.execute(
            "UPDATE orders SET status=? WHERE order_no=?",
            (db.ORDER_CANCELLED, order_no),
        )
        conn.commit()
        return ok({"order_no": order_no, "status": db.ORDER_CANCELLED})
    finally:
        conn.close()


# ---------------- 支付回调 ----------------
@app.post("/api/pay/callback")
def pay_callback(req: PayCallbackRequest):
    order_no = (req.order_no or "").strip()
    conn = db.get_conn()
    try:
        order = conn.execute(
            "SELECT * FROM orders WHERE order_no=?", (order_no,)
        ).fetchone()
        if order is None:
            return fail("订单不存在", code=404, http_status=404)
        if req.pay_status != "success":
            return fail("支付失败，订单状态未变更")
        if req.amount is None or abs(float(req.amount) - float(order["total_amount"])) > 0.01:
            return fail("支付金额与订单金额不一致")
        if not req.trade_no:
            return fail("交易流水号不能为空")
        if order["status"] == db.ORDER_PAID:
            return fail("订单已支付，请勿重复回调")
        conn.execute(
            "UPDATE orders SET status=? WHERE order_no=?", (db.ORDER_PAID, order_no)
        )
        conn.execute(
            "INSERT INTO pay_records(order_no,trade_no,amount,status,created_at) "
            "VALUES(?,?,?,?,?)",
            (order_no, req.trade_no, req.amount, "success",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        return ok({"order_no": order_no, "status": db.ORDER_PAID, "trade_no": req.trade_no})
    finally:
        conn.close()
