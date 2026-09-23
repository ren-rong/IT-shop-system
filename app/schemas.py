"""Pydantic 请求模型。字段保持宽松，业务校验在路由内完成并返回统一业务码。"""
from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None


class UserAddRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None


class GoodsAddRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None


class GoodsUpdateRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None


class OrderCreateRequest(BaseModel):
    goods_id: Optional[int] = None
    quantity: Optional[int] = None


class PayCallbackRequest(BaseModel):
    order_no: Optional[str] = None
    amount: Optional[float] = None
    pay_status: Optional[str] = None
    trade_no: Optional[str] = None
