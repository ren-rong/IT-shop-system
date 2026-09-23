"""页面基类：封装常用操作与显式等待，所有页面继承。"""


class BasePage:
    def __init__(self, page):
        self.page = page

    def goto(self, url):
        self.page.goto(url, wait_until="domcontentloaded")

    def fill(self, locator, text):
        self.page.fill(locator, "" if text is None else str(text))

    def click(self, locator):
        self.page.click(locator)

    def text(self, locator):
        return self.page.text_content(locator)

    def is_visible(self, locator):
        return self.page.is_visible(locator)

    def wait_visible(self, locator, timeout=10000):
        self.page.wait_for_selector(locator, state="visible", timeout=timeout)

    # ---------------- 显式等待（避免异步请求未完成就断言） ----------------
    def wait_text_present(self, locator, timeout=10000):
        """等待元素出现非空文本（成功/失败提示均适用）。"""
        self.page.wait_for_function(
            "(sel) => { const el = document.querySelector(sel);"
            " return !!(el && el.textContent.trim().length); }",
            arg=locator,
            timeout=timeout,
        )

    def wait_row(self, tbody_selector, text, timeout=10000):
        """等待表格中出现包含指定文本的行，超时返回 False。"""
        try:
            self.page.locator(
                f"{tbody_selector} tr", has_text=text
            ).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def wait_row_count_atleast(self, tbody_selector, minimum, timeout=10000):
        """等待表格行数达到 minimum。"""
        self.page.wait_for_function(
            "([sel, min]) => document.querySelectorAll(sel).length >= min",
            arg=[f"{tbody_selector} tr", minimum],
            timeout=timeout,
        )

    def row_count(self, tbody_selector):
        return self.page.locator(f"{tbody_selector} tr").count()
