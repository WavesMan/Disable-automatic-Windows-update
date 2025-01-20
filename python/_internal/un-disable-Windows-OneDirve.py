import subprocess
import ctypes
import sys

def is_admin():
    """检查是否以管理员身份运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def write_registry():
    """写入注册表内容"""
    commands = [
        'reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\OneDrive" /v "DisableFileSyncNGSC" /t REG_DWORD /d 0 /f',
    ]

    for cmd in commands:
        try:
            # 使用 cmd 直接执行 reg add 命令
            subprocess.run(cmd, shell=True, check=True)
            print(f"成功执行: {cmd}")
        except subprocess.CalledProcessError as e:
            print(f"执行失败: {cmd}\n错误信息: {e}")

if __name__ == "__main__":
    if is_admin():
        write_registry()
    else:
        # 以管理员身份重新运行脚本
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)