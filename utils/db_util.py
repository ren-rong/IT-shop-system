"""
数据库校验工具（直连被测 SQLite 库）：
测试断言不能只看接口返回，需通过本工具核对数据是否真正落库/变更。
"""
import os
import sqlite3

from utils.config_loader import ROOT_DIR, CONFIG
from utils.log_util import logger

DB_PATH = os.path.join(ROOT_DIR, CONFIG["database"]["path"])


class DBUtil:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, timeout=10)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=5000;")

    def query_one(self, sql, args=()):
        row = self.conn.execute(sql, args).fetchone()
        return dict(row) if row else None

    def query_all(self, sql, args=()):
        return [dict(r) for r in self.conn.execute(sql, args).fetchall()]

    def count(self, sql, args=()):
        return self.conn.execute(sql, args).fetchone()[0]

    def execute(self, sql, args=()):
        logger.info(f"DB execute: {sql} | {args}")
        cur = self.conn.execute(sql, args)
        self.conn.commit()
        return cur

    def close(self):
        self.conn.close()
