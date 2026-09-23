"""
SQLite 数据访问层
- 零配置：Python 内置 sqlite3，无需安装数据库，clone 仓库即可运行
- 开启 WAL，支持「被测服务进程写 + 测试进程读」并发校验
- 教学项目密码使用 sha256 摘要（生产环境应使用 bcrypt/argon2 加盐）
"""
import os
import sqlite3
import hashlib
from datetime import datetime

# 数据库文件固定在 app 目录下
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ecommerce.db")

# 订单状态常量
ORDER_PENDING = "PENDING"
ORDER_PAID = "PAID"
ORDER_CANCELLED = "CANCELLED"


def hash_password(password: str) -> str:
    return hashlib.sha256(str(password).encode("utf-8")).hexdigest()


def get_conn():
    """每次返回一个新连接（短连接），调用方负责关闭。"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_db():
    """建表 + 初始化种子数据（幂等，可重复执行）。"""
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            goods_id INTEGER NOT NULL,
            goods_name TEXT,
            quantity INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS pay_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL,
            trade_no TEXT,
            amount REAL,
            status TEXT,
            created_at TEXT
        );
        """
    )
    conn.commit()
    _seed(conn)
    conn.close()


def _seed(conn):
    """插入基础账号与商品，已存在则跳过。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users = [
        ("admin", hash_password("123456"), "13800000000", "admin"),
        ("testadmin", hash_password("123456"), "13800000001", "admin"),
        ("buyer", hash_password("123456"), "13800000002", "user"),
    ]
    for u in users:
        conn.execute(
            "INSERT OR IGNORE INTO users(username,password,phone,role,created_at) "
            "VALUES(?,?,?,?,?)",
            (u[0], u[1], u[2], u[3], now),
        )

    goods = [
        ("机械键盘", 199.00, 100),
        ("无线鼠标", 89.50, 200),
        ("4K显示器", 1299.00, 50),
        ("USB-C数据线", 29.90, 500),
    ]
    for g in goods:
        conn.execute(
            "INSERT OR IGNORE INTO goods(name,price,stock,created_at) VALUES(?,?,?,?)",
            (g[0], g[1], g[2], now),
        )
    conn.commit()


def reset_database():
    """丢弃所有表并重建（测试会话开始时使用，保证每次都是干净环境）。"""
    conn = get_conn()
    conn.executescript(
        """
        DROP TABLE IF EXISTS pay_records;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS goods;
        DROP TABLE IF EXISTS users;
        """
    )
    conn.commit()
    conn.close()
    init_db()


if __name__ == "__main__":
    init_db()
    print(f"数据库初始化完成: {DB_PATH}")
