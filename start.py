"""校园二手交易平台一键启动脚本"""
import subprocess
import sys
import os
import time
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

BACKEND_PORT = 8000
FRONTEND_PORT = 5173

processes = []


def check_port(port):
    """检测端口是否被占用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_port(port, timeout=30):
    """等待服务端口就绪"""
    start = time.time()
    while time.time() - start < timeout:
        if check_port(port):
            return True
        time.sleep(0.5)
    return False


def start_backend():
    print("[1/2] 启动后端服务...")
    log = open(os.path.join(BACKEND_DIR, "backend.log"), "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
        cwd=BACKEND_DIR,
        stdout=log,
        stderr=log,
    )
    processes.append(("后端", proc, log))
    if wait_port(BACKEND_PORT):
        print(f"      后端已启动 → http://localhost:{BACKEND_PORT}")
        print(f"      API 文档  → http://localhost:{BACKEND_PORT}/docs")
    else:
        print("      后端启动失败，请查看 backend/backend.log")


def start_frontend():
    print("[2/2] 启动前端服务...")
    log = open(os.path.join(FRONTEND_DIR, "frontend.log"), "w", encoding="utf-8")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=log,
        stderr=log,
    )
    processes.append(("前端", proc, log))
    if wait_port(FRONTEND_PORT):
        print(f"      前端已启动 → http://localhost:{FRONTEND_PORT}")
    else:
        print("      前端启动失败，请查看 frontend/frontend.log")


def stop_all():
    print("\n正在停止所有服务...")
    for name, proc, log in processes:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()
        print(f"      {name}已停止")
    processes.clear()


def main():
    print("=" * 50)
    print("  校园二手交易平台 - 一键启动")
    print("=" * 50)

    if check_port(BACKEND_PORT):
        print(f"端口 {BACKEND_PORT} 已被占用，后端可能已在运行")
    if check_port(FRONTEND_PORT):
        print(f"端口 {FRONTEND_PORT} 已被占用，前端可能已在运行")

    start_backend()
    start_frontend()

    print("-" * 50)
    print("所有服务已启动，按 Ctrl+C 停止")
    print("-" * 50)

    try:
        while True:
            time.sleep(1)
            # 检测子进程是否意外退出
            for name, proc, log in processes:
                if proc.poll() is not None:
                    print(f"[警告] {name}进程已退出 (code={proc.returncode})，请查看日志")
    except KeyboardInterrupt:
        stop_all()


if __name__ == "__main__":
    main()
