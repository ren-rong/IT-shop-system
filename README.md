# 电商后台「接口 + WebUI」一体化自动化测试框架

一套**开箱即用、零外部依赖**的自动化测试实战项目：内置一个 FastAPI 电商被测系统（后端接口 + 前端管理页面 + SQLite 数据库），并基于 **Pytest** 同时落地**接口自动化**与 **WebUI 自动化**。`pytest` 一条命令即可自动重置数据、拉起被测服务、执行用例、校验数据库、生成报告、清理环境并关闭服务。

- 测试结果：**71 个用例连续多次运行 100% 通过**（接口 57 + WebUI 14）
- 正常 / 异常用例比例约 **7 : 3**
- 断言覆盖 **HTTP 状态码 → 业务码与关键字段 → 数据库真实状态** 三层
- 报告：自包含 **HTML 报告**（pytest-html）+ **Allure** 原始结果
- 失败留存：完整请求/响应日志、自动全页截图、操作录屏、环境信息
- CI：内置 **GitHub Actions**（提交触发 + 每日北京时间 08:00 定时回归）

---

## 一、技术栈

| 分类 | 技术 |
| --- | --- |
| 被测服务 | FastAPI、Uvicorn、Pydantic |
| 数据库 | SQLite（Python 内置，`WAL` 模式，零安装） |
| 鉴权 | JWT（PyJWT，Bearer Token） |
| 接口测试 | Pytest、Requests |
| WebUI 测试 | Pytest、Playwright（Chromium，PO 页面对象模式） |
| 报告 | pytest-html（自包含）、Allure |
| CI/CD | GitHub Actions |
| 其他 | PyYAML（配置）、Faker（测试数据） |

> 选择 SQLite 而非 MySQL，是为了让任何人 **clone 后无需安装/配置数据库即可运行**；DB 工具层基于标准 DB-API，可平滑替换为 MySQL（pymysql）。

---

## 二、覆盖范围

| 模块 | 接口 | 用例数 |
| --- | --- | --- |
| 登录 | `POST /api/login`、受保护接口鉴权 | 12 |
| 用户 | 用户信息、用户列表/搜索、新增、详情 | 12 |
| 商品 | 列表/搜索、详情、新增、更新、删除 | 14 |
| 订单 | 下单、列表、详情、取消（含库存扣减/恢复） | 12 |
| 支付回调 | 成功回调、金额校验、重复回调、失败回调 | 7 |
| **接口合计** | | **57** |
| WebUI | 登录页、商品页、订单页、用户页 | **14** |

---

## 三、目录结构

```
.
├── app/                        # 被测电商系统
│   ├── main.py                 # FastAPI 路由（登录/用户/商品/订单/支付回调）
│   ├── database.py             # SQLite 建表、种子数据、重置
│   ├── auth.py                 # JWT 签发与校验
│   ├── schemas.py              # Pydantic 请求模型
│   └── static/                 # 前端页面（login/goods/orders/users.html + common.js）
├── config/
│   └── settings.yaml           # 环境地址、服务端口、数据库路径、主账号
├── utils/                      # 工具层
│   ├── request_util.py         # 请求封装：统一 base_url、自动带 Token、日志
│   ├── db_util.py              # 数据库校验工具（查询/计数/执行）
│   ├── log_util.py             # 日志（控制台 + 文件）
│   └── config_loader.py        # 配置加载
├── api/                        # 接口封装层（API Object，只封装调用）
├── pages/                      # WebUI 页面对象层（Page Object）
├── testcases/
│   ├── api/                    # 接口测试用例
│   └── ui/                     # WebUI 测试用例
├── reports/report.html         # 自包含 HTML 报告（运行后生成）
├── allure-results/             # Allure 原始结果（运行后生成）
├── logs/                       # 运行/服务/请求响应日志
├── screenshots/                # 失败自动截图
├── videos/                     # UI 自动录屏
├── .github/workflows/pytest-ci.yml   # GitHub Actions 流水线
├── conftest.py                 # 全局夹具：服务编排、Token、DB、浏览器
├── run.py                      # 统一执行入口
├── pytest.ini
└── requirements.txt
```

**分层思想**：配置 / 工具 / 接口封装 / 页面对象 / 用例各司其职。业务接口变更只改 `api`，页面改版只改 `pages`，用例只描述业务与断言，维护成本低。

---

## 四、快速开始

### 1. 环境要求
- Python **3.9 ~ 3.12**（本项目在 3.11 验证）
- Git

### 2. 克隆并进入目录
```bash
git clone <your-repo-url>
cd ecommerce_api_auto
```

### 3. 创建并激活虚拟环境
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. 安装依赖
```bash
pip install -r requirements.txt
```

### 5. 安装 Playwright 浏览器（仅 WebUI 需要）
```bash
playwright install chromium
```

### 6. 一键运行（接口 + WebUI）
```bash
python run.py
```
> 无需手动启动后端：`conftest` 会自动重置数据库、拉起 Uvicorn、等待就绪；结束后自动清理数据并关闭服务。

执行完成后打开报告：
```
reports/report.html
```

---

## 五、运行方式

| 命令 | 说明 |
| --- | --- |
| `python run.py` 或 `python run.py all` | 接口 + WebUI 全量回归 |
| `python run.py api` | 仅接口用例（57） |
| `python run.py ui` | 仅 WebUI 用例（14） |
| `python run.py smoke` | 仅冒烟集合（核心主流程） |
| `pytest -m smoke` | 直接用 marker 跑冒烟 |
| `pytest testcases/api/test_order.py` | 跑单个文件 |
| `pytest -k "pay"` | 按关键字筛选 |

### 可选环境变量
```bash
# JWT 密钥（不设置使用内置默认值，仅测试用途）
# Windows PowerShell
$env:JWT_SECRET="your_secret"
# macOS/Linux
export JWT_SECRET="your_secret"
```

---

## 六、三层断言（核心设计）

每个关键用例都包含三层校验，**绝不只看接口返回**：

```python
# 第一层：HTTP 状态码
assert resp.status_code == 200
# 第二层：业务码 + 关键字段
assert body["code"] == 200
assert body["data"]["order_no"].startswith("NO")
# 第三层：数据库真实状态
row = db.query_one("SELECT * FROM orders WHERE order_no=?", (order_no,))
assert row is not None and row["status"] == "PENDING"
```

典型数据库校验：
- 新增用户/商品后，`SELECT` 确认数据真正落库；
- 下单后校验商品库存**扣减**，取消后校验库存**恢复**；
- 支付成功后校验订单 `PAID` 且生成支付记录；
- 异常路径（金额错误 / 库存不足 / 重复回调）校验**未产生脏数据**。

---

## 七、测试数据隔离与清理

1. **会话开始**：`reset_database()` 重建所有表并恢复种子数据，保证每次都是干净、确定的环境；
2. **数据标识**：自动化新增数据统一前缀 `auto_`（接口 `auto_user_/auto_goods_`，UI `auto_ui_`），与种子/手工数据隔离；
3. **用例独立**：用例不依赖其他用例产生的数据，需要前置数据则在本用例内动态创建；
4. **会话结束**：自动删除订单、支付记录及所有 `auto_` 数据，验证结果为「仅保留 3 个种子用户、4 个种子商品，订单/支付记录为 0」；
5. **失败回滚**：库存不足等异常路径事务回滚，不产生订单、库存不变。

---

## 八、Token 管理

- 会话级夹具 `admin_token`：整个测试会话**只登录一次**，缓存 Token；
- `RequestUtil` 在请求头**自动注入** `Authorization: Bearer <token>`，用例无需关心；
- 无 Token / Token 无效访问受保护接口，统一返回 `401`；
- JWT 设置过期时间，扩展时可在响应 `401` 时自动刷新。

---

## 九、测试报告

### HTML 报告（默认，自包含单文件）
```
reports/report.html
```
浏览器直接打开，含用例结果、耗时、日志与环境元信息。

### Allure 报告
运行时已生成 `allure-results`，本机安装 Allure 命令行后：
```bash
allure serve allure-results
```

### 失败排查三件套
- `logs/test_run.log`、`logs/server.log`：完整请求方法/URL/入参、响应状态/响应体、服务日志与环境信息；
- `screenshots/FAIL_*.png`：失败用例自动全页截图；
- `videos/*.webm`：每个 UI 用例的操作录屏。

---

## 十、CI/CD（GitHub Actions）

`.github/workflows/pytest-ci.yml`：
- `push` / `pull_request` 自动执行接口 + WebUI；
- `schedule` 每日 **UTC 00:00（北京时间 08:00）**定时全量回归；
- 自动安装依赖与 Playwright 浏览器（无头），上传 HTML 报告与失败截图为 Artifact。

接入 Jenkins 同理：安装 Python 与 Playwright 后执行 `pytest testcases --html=reports/report.html --self-contained-html`。

---

## 十一、简历亮点（可直接引用）

> **电商后台「接口 + WebUI」一体化自动化测试框架**（Python / Pytest / Requests / Playwright / FastAPI / SQLite / Allure / GitHub Actions）
> - 从零搭建 FastAPI 电商被测系统，覆盖登录、用户、商品、订单、支付回调全链路，落地 **71 条**自动化用例（接口 57 + UI 14），正常/异常约 7:3，连续多次运行 100% 通过；
> - 设计并落地**三层断言**（HTTP 状态码、业务码与关键字段、数据库状态），接口校验深入到库存扣减/恢复、订单状态流转与支付落库，避免「只看返回」的漏测；
> - 封装统一请求客户端，会话级 Token 管理与自动注入；采用 **PO 模式** 解耦页面元素与用例，页面改版仅需维护 Page 层；
> - 建立测试数据隔离与全生命周期治理：前缀标识、会话级重置、失败回滚、结束自动清理，杜绝脏数据与用例相互依赖；
> - 失败自动留存请求/响应日志、全页截图与录屏；接入 GitHub Actions 实现提交触发与每日定时回归，报告与截图自动归档。

---

## 十二、面试高频 Q&A

- **目录为什么分层？** 配置、工具、接口、页面、用例解耦；接口变更改 `api`、页面改版改 `pages`，用例稳定，可维护性高。
- **Token 怎么管理？** 会话级夹具只登录一次并缓存，请求客户端统一注入；减少重复登录，失效时统一处理 401/刷新。
- **测试数据怎么隔离？** 会话开始重置到确定状态，自动化数据带 `auto_` 前缀，结束自动清理，失败事务回滚，不污染环境。
- **如何避免用例互相依赖？** 每条用例自洽，前置数据在本用例创建；不依赖其他用例的执行结果与顺序。
- **为什么用 Playwright？** 自带自动等待、自动装浏览器、原生支持录屏/网络拦截，CI 部署简单，比 Selenium 更稳定、样板更少。
- **UI 为什么还要查数据库？** 页面提示成功不代表真正落库；页面 + 文案 + 数据库三层校验可发现前后端不一致缺陷。

---

## 十三、进阶方向

- 用例分级（P0/P1/P2）与可配置冒烟集合；
- 失败自动重试与失败分类（环境 / 数据 / 代码）；
- 接入测试数据工厂（Faker + Factory）统一造数；
- 增量覆盖率（coverage / 接口变更影响面分析）；
- DB 层抽象，支持 MySQL/PostgreSQL 多环境切换；
- 支付回调签名校验、并发下单与库存超卖测试。
