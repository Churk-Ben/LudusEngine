from ssl import socket_error
from src.Server import app, socketio
from src.Logger import get_logger
from src.Config import load_config
import webbrowser
import platform
import os
import threading

try:
    import webview
except ImportError:
    webview = None

log = get_logger("APP")
log.info("-" * 80)
log.info(f"操作系统 - System: {platform.system()}")
log.info(f"操作系统版本 - Release: {platform.release()}")
log.info(f"详细版本 - Version: {platform.version()}")
log.info(f"硬件架构 - Machine: {platform.machine()}")
log.info(f"处理器 - Processor: {platform.processor()}")
log.info("-" * 80)
log.info(f"平台信息汇总 - Platform: {platform.platform()}")


def open_browser_in_app_mode(url):
    browser_list = ["msedge.exe", "chrome.exe", "firefox.exe"]
    if platform.system() == "Windows":
        log.info(f"Windows 系统, 尝试app模式开启应用.")
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

    else:
        log.info(f"非 Windows 系统, 直接打开浏览器.")
        webbrowser.open_new(url)


def browser_main():
    # 加载配置
    config = load_config()
    log.info(f"配置加载完成: {config}")

    DEBUG = os.getenv("debug", "0") == "1"
    log.info(f"DEBUG 模式: {DEBUG}")

    if DEBUG:
        if not os.environ.get("WERKZEUG_RUN_MAIN"):
            open_browser_in_app_mode("http://localhost:5000")
        try:
            socketio.run(app, host="127.0.0.1", port=5000, debug=True)
        except SystemExit:
            log.info("服务器已成功关闭")

    else:
        if webview:
            log.info("检测到 pywebview, 启动桌面应用模式.")
            # 启动服务器线程
            t = threading.Thread(
                target=lambda: socketio.run(
                    app, host="127.0.0.1", port=5000, debug=False
                )
            )
            t.daemon = True
            t.start()

            # 启动 webview
            webview.create_window(
                "Ludus Engine", "http://localhost:5000", width=1280, height=800
            )
            webview.start()
        else:
            open_browser_in_app_mode("http://localhost:5000")
            try:
                socketio.run(app, host="127.0.0.1", port=5000, debug=False)
            except SystemExit:
                log.info("服务器已成功关闭")


if __name__ == "__main__":
    # 打包后资源路径兼容
    # def base_path(*p):
    #     return os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), *p)
    browser_main()
