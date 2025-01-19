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
        'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "FlightSettingsMaxPauseDays" /t REG_DWORD /d 18300 /f',
        'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseFeatureUpdatesStartTime" /t REG_SZ /d "2023-07-07T10:00:52Z" /f',
        'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseFeatureUpdatesEndTime" /t REG_SZ /d "2050-01-01T00:00:00Z" /f',
        'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseQualityUpdatesStartTime" /t REG_SZ /d "2023-07-07T10:00:52Z" /f',
        'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseQualityUpdatesEndTime" /t REG_SZ /d "2050-01-01T00:00:00Z" /f',
        'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseUpdatesStartTime" /t REG_SZ /d "2023-07-07T09:59:52Z" /f',
        'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseUpdatesExpiryTime" /t REG_SZ /d "2050-01-01T00:00:00Z" /f',
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