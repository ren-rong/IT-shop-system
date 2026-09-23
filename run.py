"""
项目统一执行入口
用法：
    python run.py            # 接口 + UI 全量
    python run.py api        # 仅接口
    python run.py ui         # 仅 WebUI
    python run.py smoke      # 仅冒烟集合
"""
import sys
import pytest

from utils.config_loader import ROOT_DIR  # noqa: F401


def build_args(scope):
    args = [
        "testcases",
        "-v",
        "--html=reports/report.html",
        "--self-contained-html",
        "--alluredir=allure-results",
        "--clean-alluredir",
    ]
    if scope == "api":
        args += ["-m", "api"]
    elif scope == "ui":
        args += ["-m", "ui"]
    elif scope == "smoke":
        args += ["-m", "smoke"]
    return args


if __name__ == "__main__":
    scope = sys.argv[1] if len(sys.argv) > 1 else "all"
    if scope not in ("all", "api", "ui", "smoke"):
        print("用法: python run.py [all|api|ui|smoke]")
        sys.exit(1)
    exit_code = pytest.main(build_args(scope))
    print(f"\n执行结束，HTML 报告: reports/report.html (scope={scope}, exit={exit_code})")
    sys.exit(exit_code)
