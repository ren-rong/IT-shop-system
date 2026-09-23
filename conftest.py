"""
全局夹具与编排：
1. 会话开始：重置数据库 -> 若服务未启动则自动拉起 uvicorn -> 等待就绪
2. 会话结束：清理自动化测试数据 -> 关闭由测试拉起的服务
3. 提供：数据库校验连接、登录 Token、Playwright 浏览器/页面（失败自动截图+录屏）
"""
import os
import sys
import time
import subprocess
import platform

import pytest
import requests

# 确保项目根目录在 sys.path
from utils.config_loader import ROOT_DIR, CONFIG, base_url
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.request_util import RequestUtil
from utils.db_util import DBUtil
from utils.log_util import logger
from api.login_api import LoginApi
from pages.login_page import LoginPage

for _d in ("logs", "screenshots", "videos", "reports"):
    os.makedirs(os.path.join(ROOT_DIR, _d), exist_ok=True)


# ---------------- 用例结果钩子（失败检测） ----------------
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


# ---------------- 按目录自动打 api / ui 标记 ----------------
def pytest_collection_modifyitems(config, items):
    for item in items:
        path = str(item.fspath).replace("/", os.sep)
        if os.path.join("testcases", "ui") in path:
            item.add_marker(pytest.mark.ui)
        elif os.path.join("testcases", "api") in path:
            item.add_marker(pytest.mark.api)


# ---------------- 服务与数据库编排 ----------------
def _service_alive():
    try:
        r = requests.get(base_url() + "/api/goods", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _start_server():
    host = CONFIG["server"]["host"]
    port = str(CONFIG["server"]["port"])
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app",
           "--host", host, "--port", port, "--log-level", "warning"]
    logf = open(os.path.join(ROOT_DIR, "logs", "server.log"), "w", encoding="utf-8")
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    logger.info(f"启动被测服务: {' '.join(cmd)}")
    return subprocess.Popen(
        cmd, cwd=ROOT_DIR, stdout=logf, stderr=subprocess.STDOUT,
        creationflags=creation_flags,
    )


def _wait_service(timeout=40):
    for _ in range(timeout * 2):
        if _service_alive():
            logger.info(f"被测服务已就绪: {base_url()}")
            return True
        time.sleep(0.5)
    return False


def _stop_server(proc):
    try:
        proc.terminate()
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
    logger.info("被测服务已关闭")


def _cleanup_test_data():
    d = DBUtil()
    try:
        d.execute("DELETE FROM pay_records")
        d.execute("DELETE FROM orders")
        d.execute("DELETE FROM goods WHERE name LIKE 'auto_%'")
        d.execute("DELETE FROM users WHERE username LIKE 'auto_%'")
        logger.info("自动化测试数据清理完成")
    finally:
        d.close()


@pytest.fixture(scope="session", autouse=True)
def test_environment():
    # 记录环境信息（失败排查 / 报告留存）
    logger.info(
        f"环境信息 | OS={platform.platform()} | Python={sys.version.split()[0]} "
        f"| base_url={base_url()}"
    )
    # 1) 重置数据库到干净状态（在启动服务前，避免锁）
    import app.database as srv_db
    srv_db.reset_database()
    logger.info("数据库已重置为初始状态")

    # 2) 服务未运行则自动拉起
    proc = None
    if not _service_alive():
        proc = _start_server()
    if not _wait_service():
        raise RuntimeError("被测服务启动超时，请查看 logs/server.log")

    yield

    # 3) 清理数据
    _cleanup_test_data()
    # 4) 关闭由测试拉起的服务
    if proc is not None:
        _stop_server(proc)


# ---------------- 接口测试夹具 ----------------
@pytest.fixture(scope="session")
def db(test_environment):
    d = DBUtil()
    yield d
    d.close()


@pytest.fixture(scope="session")
def admin_token(test_environment):
    """会话级登录：只登录一次，全局复用 Token。"""
    username = CONFIG["admin"]["username"]
    password = CONFIG["admin"]["password"]
    resp = LoginApi().login(username, password)
    body = resp.json()
    assert body["code"] == 200, f"测试主账号登录失败: {body}"
    token = body["data"]["token"]
    RequestUtil.set_token(token)
    logger.info(f"测试主账号登录成功，Token 已全局注入: {username}")
    return token


# ---------------- WebUI（Playwright）夹具 ----------------
@pytest.fixture(scope="session")
def playwright_instance():
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    yield pw
    pw.stop()


@pytest.fixture(scope="session")
def browser(playwright_instance):
    b = playwright_instance.chromium.launch(headless=True)
    yield b
    b.close()


@pytest.fixture(scope="function")
def context(browser):
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        record_video_dir=os.path.join(ROOT_DIR, "videos"),
    )
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def page(context, request):
    pg = context.new_page()
    yield pg
    # 失败自动全页截图
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        safe = "".join(c if c.isalnum() else "_" for c in request.node.name)[:60]
        try:
            shot = os.path.join(ROOT_DIR, "screenshots", f"FAIL_{safe}.png")
            pg.screenshot(path=shot, full_page=True)
            logger.info(f"失败用例截图已保存: {shot}")
        except Exception as e:
            logger.warning(f"截图失败: {e}")
    pg.close()


@pytest.fixture(scope="function")
def logged_page(page, test_environment):
    """已登录的页面：自动完成登录并等待进入商品页。"""
    lp = LoginPage(page)
    lp.goto_login()
    lp.login(CONFIG["admin"]["username"], CONFIG["admin"]["password"])
    lp.wait_until_logged_in()
    return page
