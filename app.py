import os
import platform
import threading
import webbrowser
from pathlib import Path

from src.Config import load_config
from src.Logger import get_logger
from src.Server import app, socketio

try:
    import webview
except ImportError:
    webview = None

BASE = Path(__file__).resolve().parent
STATIC_DIR = BASE / "res" / "app" / "static"

log = get_logger("APP")
log.info("-" * 80)
log.info(f"操作系统 - System: {platform.system()}")
log.info(f"操作系统版本 - Release: {platform.release()}")
log.info(f"详细版本 - Version: {platform.version()}")
log.info(f"硬件架构 - Machine: {platform.machine()}")
log.info(f"处理器 - Processor: {platform.processor()}")
log.info("-" * 80)
log.info(f"平台信息汇总 - Platform: {platform.platform()}")


def override_index_zoom():
    sys_platform = platform.system()
    if sys_platform == "Windows":
        ZOOM = os.getenv("ZOOM", "1.0")
    else:
        ZOOM = os.getenv("ZOOM", "1.5")
    log.debug(f"配置的缩放比例 - Zoom: {ZOOM}")

    log.debug(f"已注入缩放比例.")


def open_browser_in_app_mode(url):
    if platform.system() == "Windows":
        log.info(f"Windows 系统, 尝试app模式开启应用.")
        browser_list = [
            "msedge.exe",
            "chrome.exe",
            "firefox.exe",
        ]
        for browser in browser_list:
            try:
                os.system(f'start "" {browser} --app="{url}"')
                log.info(f"通过app模式成功打开{browser}.")
                break
            except Exception as e:
                log.warning(f"尝试通过app模式打开{browser}失败: {e}")
        else:
            log.warning(f"尝试通过app模式打开浏览器失败, 未找到可用浏览器.")
            webbrowser.open_new(url)

    elif platform.system() == "Linux":
        log.info(f"Linux 系统, 尝试app模式开启应用.")
        browser_list = [
            "google-chrome",
            "microsoft-edge-stable",
            "microsoft-edge",
            "chromium",
            "chromium-browser",
        ]
        for browser in browser_list:
            if os.system(f"which {browser} > /dev/null 2>&1") == 0:
                try:
                    os.system(f'{browser} --app="{url}" &')
                    log.info(f"通过app模式成功打开{browser}.")
                    break
                except Exception as e:
                    log.warning(f"尝试通过app模式打开{browser}失败: {e}")
        else:
            log.warning(f"尝试通过app模式打开浏览器失败, 未找到可用浏览器.")
            webbrowser.open_new(url)

    else:
        log.info(f"非 Windows/Linux 系统, 直接打开浏览器.")
        webbrowser.open_new(url)


def main():
    config = load_config()
    log.info(f"配置加载完成: {config}")

    DEBUG = os.getenv("debug", "0") == "1"
    MODE = os.getenv("mode", "app")
    log.info(f"DEBUG 模式: {DEBUG}, 运行模式: {MODE}")

    override_index_zoom()

    if DEBUG:
        if MODE == "app":
            log.debug("测试浏览器APP模式.")
            if not os.environ.get("WERKZEUG_RUN_MAIN"):
                open_browser_in_app_mode("http://localhost:5000")
            try:
                socketio.run(app, host="127.0.0.1", port=5000, debug=True)
            except SystemExit:
                log.info("服务器已成功关闭")

        elif MODE == "browser":
            log.debug("测试浏览器普通模式.")
            if not os.environ.get("WERKZEUG_RUN_MAIN"):
                webbrowser.open_new("http://localhost:5000")
            try:
                socketio.run(app, host="127.0.0.1", port=5000, debug=True)
            except SystemExit:
                log.info("服务器已成功关闭")

        elif MODE == "desktop":
            log.debug("测试桌面应用模式.")
            if webview:
                t = threading.Thread(
                    target=lambda: socketio.run(
                        app, host="127.0.0.1", port=5000, debug=True, use_reloader=False
                    )
                )
                t.daemon = True
                t.start()

                window = webview.create_window(
                    "Ludus Engine",
                    "http://localhost:5000",
                    width=1280,
                    height=800,
                    zoomable=True,
                )
                webview.start()

            else:
                log.warning("未检测到 pywebview, 无法启动桌面应用模式.")
                return

        else:
            log.warning(f"未知运行模式: {MODE}, 无法启动应用.")
            return

    else:
        if webview:
            log.info("检测到 pywebview, 启动桌面应用模式.")
            log.debug("启动服务器线程")
            t = threading.Thread(
                target=lambda: socketio.run(
                    app, host="127.0.0.1", port=5000, debug=False
                )
            )
            t.daemon = True
            t.start()

            log.debug("启动 webview 窗口")
            window = webview.create_window(
                "Ludus Engine",
                "http://localhost:5000",
                width=1280,
                height=800,
                zoomable=True,
            )
            webview.start()

        else:
            log.info("未检测到 pywebview, 启动浏览器模式.")
            log.debug("启动服务器线程")
            t = threading.Thread(
                target=lambda: socketio.run(
                    app, host="127.0.0.1", port=5000, debug=False
                )
            )
            t.daemon = True
            t.start()

            log.debug("启动浏览器线程")
            open_browser_in_app_mode("http://localhost:5000")


if __name__ == "__main__":
    main()
