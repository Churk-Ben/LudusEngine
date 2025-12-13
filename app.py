import eventlet
from eventlet import patcher

# Use original threading.Thread to ensure server runs in a real OS thread,
# preventing blocking issues with native GUI loops (pywebview) or main thread exit.
OriginalThread = patcher.original("threading").Thread

eventlet.monkey_patch()

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
    """
    配置应用的缩放比例

    原理参考浏览器 Ctrl+滚轮缩放：
    缩放的本质是改变 CSS 像素到设备像素的动态映射 (devicePixelRatio)。
    - 100% 缩放: 1 CSS 像素 = 1 设备像素
    - 150% 缩放: 1 CSS 像素 = 1.5 设备像素

    此处通过环境变量设置底层 GUI 框架的缩放因子，以模拟此效果。
    """
    sys_platform = platform.system()
    if sys_platform == "Linux":
        # Linux 下高分屏适配通常需要手动调整，默认 1.5
        ZOOM = os.getenv("ZOOM", "1.5")
    else:
        # Windows/Mac 通常系统级 DPI 适配较好，默认 1.0
        ZOOM = os.getenv("ZOOM", "1.0")

    # 确保环境变量被设置，供后续流程或子进程使用
    os.environ["ZOOM"] = ZOOM
    log.debug(f"配置的缩放比例 - Zoom: {ZOOM}")

    try:
        # 尝试应用到常见 GUI 框架的环境变量

        # 1. QT 框架 (QtWebEngine / PySide / PyQt)
        # QT_SCALE_FACTOR 直接定义了物理像素与逻辑像素的比例
        os.environ["QT_SCALE_FACTOR"] = ZOOM

        # 2. GTK 框架 (WebKitGTK)
        # GDK_SCALE 只能是整数 (1, 2, ...)，用于处理整数倍的 HiDPI
        # GDK_DPI_SCALE 可以是浮点数，主要影响字体和 UI 元素的缩放
        # 这里我们保守策略：只设置 DPI 缩放，避免强制修改 GDK_SCALE 导致界面错乱
        os.environ["GDK_DPI_SCALE"] = ZOOM

        # 3. Chromium 标志 (如果有传递机制)
        # 许多基于 Chromium 的应用支持 --force-device-scale-factor
        # pywebview 可能通过 QT_WEBENGINE_CHROMIUM_FLAGS 传递
        os.environ["QT_WEBENGINE_CHROMIUM_FLAGS"] = (
            f"--force-device-scale-factor={ZOOM}"
        )

    except Exception as e:
        log.warning(f"应用缩放配置时发生错误: {e}")


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


import socket
import time


def wait_for_server(host, port, timeout=10):
    """Wait for the server to be available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.1)
    return False


def main():
    config = load_config()
    log.info(f"配置加载完成: {config}")

    DEBUG = os.getenv("debug", "0") == "1"
    MODE = os.getenv("mode", "app")
    log.info(f"DEBUG 模式: {DEBUG}, 运行模式: {MODE}")

    override_index_zoom()

    host = "127.0.0.1"
    port = 5000
    server_url = f"http://{host}:{port}"

    if DEBUG:
        # In Debug mode, Flask's reloader will restart the process.
        # We handle browser opening logic carefully.

        if MODE == "app":
            log.debug("测试浏览器APP模式.")
            # Only open browser if this is the main process (before reload) OR if reloader is disabled
            # But with reloader, the server starts in the child process.
            # To avoid race condition, we should start a thread that waits for server then opens browser.

            def open_browser_delayed():
                if wait_for_server(host, port):
                    open_browser_in_app_mode(server_url)
                else:
                    log.error("Server failed to start in time.")

            # Only start this thread if we are in the reloader process (server is running)
            # or if we are just starting and expect the server to come up.
            # Common flask pattern: open browser in the main block if WERKZEUG_RUN_MAIN is set.

            if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
                # Use OriginalThread to avoid interference with eventlet patching if any
                OriginalThread(target=open_browser_delayed, daemon=True).start()

            try:
                socketio.run(app, host=host, port=port, debug=True)
            except SystemExit:
                log.info("服务器已成功关闭")

        elif MODE == "browser":
            log.debug("测试浏览器普通模式.")

            def open_browser_delayed():
                if wait_for_server(host, port):
                    webbrowser.open_new(server_url)

            if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
                OriginalThread(target=open_browser_delayed, daemon=True).start()

            try:
                socketio.run(app, host=host, port=port, debug=True)
            except SystemExit:
                log.info("服务器已成功关闭")

        elif MODE == "desktop":
            log.debug("测试桌面应用模式.")
            if webview:
                # Desktop mode usually disables reloader to avoid pywebview issues
                # Use OriginalThread to run server in a separate OS thread
                t = OriginalThread(
                    target=lambda: socketio.run(
                        app, host=host, port=port, debug=True, use_reloader=False
                    )
                )
                t.daemon = True
                t.start()

                if wait_for_server(host, port):
                    window = webview.create_window(
                        "Ludus Engine",
                        server_url,
                        width=1280,
                        height=800,
                        zoomable=True,
                    )
                    webview.start()
                else:
                    log.error("Server failed to start. Exiting.")
                    return

            else:
                log.warning("未检测到 pywebview, 无法启动桌面应用模式.")
                return

        else:
            log.warning(f"未知运行模式: {MODE}, 无法启动应用.")
            return

    else:
        # Non-Debug Mode
        if webview and MODE == "desktop":
            log.info("检测到 pywebview, 启动桌面应用模式.")
            log.debug("启动服务器线程")
            # Use OriginalThread to run server in a separate OS thread
            t = OriginalThread(
                target=lambda: socketio.run(app, host=host, port=port, debug=False)
            )
            t.daemon = True
            t.start()

            log.debug("Waiting for server to be ready...")
            if wait_for_server(host, port):
                log.debug("Server ready, starting webview")
                window = webview.create_window(
                    "Ludus Engine",
                    server_url,
                    width=1280,
                    height=800,
                    zoomable=True,
                )
                webview.start()
            else:
                log.error("Server failed to start in time.")

        else:
            # Browser or App mode (Non-Debug)
            log.info(f"启动模式: {MODE}. 启动服务器线程...")
            # Use OriginalThread
            t = OriginalThread(
                target=lambda: socketio.run(app, host=host, port=port, debug=False)
            )
            t.daemon = True
            t.start()

            log.debug("Waiting for server to be ready...")
            if wait_for_server(host, port):
                log.debug("Server ready, opening browser")
                if MODE == "browser":
                    webbrowser.open_new(server_url)
                else:
                    open_browser_in_app_mode(server_url)

                # IMPORTANT: Keep the main thread alive!
                # Since we are not using pywebview's blocking loop here,
                # and the server is in a daemon thread, we must not exit.
                try:
                    while t.is_alive():
                        t.join(1)
                except KeyboardInterrupt:
                    log.info("Stopping server...")
            else:
                log.error("Server failed to start in time.")


if __name__ == "__main__":
    main()
