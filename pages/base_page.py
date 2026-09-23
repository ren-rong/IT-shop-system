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

    def row_count(self, tbody_selector):
        return self.page.locator(f"{tbody_selector} tr").count()
