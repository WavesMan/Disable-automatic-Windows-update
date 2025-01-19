import subprocess
import ctypes
import sys

def is_admin():
    """检查是否以管理员身份运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def delete_registry():
    """删除注册表内容"""
    commands = [
        'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "FlightSettingsMaxPauseDays" /f',
        'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseFeatureUpdatesStartTime" /f',
        'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseFeatureUpdatesEndTime" /f',
        'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseQualityUpdatesStartTime" /f',
        'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseQualityUpdatesEndTime" /f',
        'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseUpdatesStartTime" /f',
        'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseUpdatesExpiryTime" /f',
    ]

    for cmd in commands:
        try:
            # 使用 cmd 直接执行 reg delete 命令
            subprocess.run(cmd, shell=True, check=True)
            print(f"成功执行: {cmd}")
        except subprocess.CalledProcessError as e:
            print(f"执行失败: {cmd}\n错误信息: {e}")

if __name__ == "__main__":
    if is_admin():
        delete_registry()
    else:
        # 以管理员身份重新运行脚本
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)