from ssl import socket_error
from src.Server import app, socketio
from src.Logger import get_logger
from src.Config import load_config
import webbrowser
import platform
import os
import sys
import webview
import threading

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

def open_app_in_webview():
    # 1. 后台线程跑 Flask-SocketIO
    t = threading.Thread(target=lambda: socketio.run(app,host="127.0.0.1",port=5000,debug=False), daemon=True)
    t.start()

    # 2. 前台的 pywebview 窗口
    webview.create_window('我的桌面应用',
                          url='http://localhost:5000',
                          width=1200, height=800,
                          resizable=True)
    webview.start()

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


