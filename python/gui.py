###########################################################################################################
###########################################################################################################
###############################              附属Python脚本            #####################################
###########################################################################################################
###########################################################################################################

import subprocess
import ctypes
import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
import darkdetect  # 用于检测系统主题
import requests  # 用于调用 GitHub API
import logging  # 用于日志记录
import shutil  # 用于文件操作

# 检查是否以管理员身份运行
def is_admin():
    """检查是否以管理员身份运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 配置日志记录
def setup_logging():
    """配置日志记录"""
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, "app.log")
    
    # 配置日志记录
    logging.basicConfig(
        level=logging.DEBUG,  # 设置日志级别为 DEBUG
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),  # 输出到文件
            logging.StreamHandler()         # 输出到控制台
        ]
    )
    
    # 设置控制台日志级别为 INFO（只显示 INFO 及以上级别的日志）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console_handler)
    
    logging.info("日志记录已初始化")

def run_script(script_name):
    """运行指定的 Python 脚本"""
    try:
        # 如果是打包后的环境，使用 sys._MEIPASS 获取资源路径
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 构建脚本的完整路径
        script_path = os.path.join(base_path, script_name)
        
        # 记录脚本运行的详细信息
        logging.debug(f"准备运行脚本: {script_path}")
        
        # 以管理员身份运行脚本
        if not is_admin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            return
        
        # 运行脚本
        subprocess.run(["python", script_path], check=True)
        logging.info(f"成功运行: {script_name}")
        print(f"成功运行: {script_name}")
    except subprocess.CalledProcessError as e:
        logging.error(f"运行失败: {script_name}\n错误信息: {e}")
        logging.exception("异常堆栈信息")  # 记录异常堆栈
        print(f"运行失败: {script_name}\n错误信息: {e}")
    except Exception as e:
        logging.error(f"未知错误: {e}")
        logging.exception("异常堆栈信息")  # 记录异常堆栈
        print(f"未知错误: {e}")

# 禁用 Windows Defender
def disable_defender():
    try:
        write_registry("HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 1)
        messagebox.showinfo("成功", "已成功禁用 Windows Defender")
    except Exception as e:
        messagebox.showerror("错误", f"禁用 Windows Defender 失败: {e}")

# 启用 Windows Defender
def un_disable_defender():
    try:
        write_registry("HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 0)
        messagebox.showinfo("成功", "已成功启用 Windows Defender")
    except Exception as e:
        messagebox.showerror("错误", f"启用 Windows Defender 失败: {e}")

# 暂停 Windows 自动更新
def disable_windows_update():
    try:
        commands = [
            'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "FlightSettingsMaxPauseDays" /t REG_DWORD /d 18300 /f',
            'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseFeatureUpdatesStartTime" /t REG_SZ /d "2023-07-07T10:00:52Z" /f',
            'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseFeatureUpdatesEndTime" /t REG_SZ /d "2050-01-01T00:00:00Z" /f',
            'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseQualityUpdatesStartTime" /t REG_SZ /d "2023-07-07T10:00:52Z" /f',
            'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseQualityUpdatesEndTime" /t REG_SZ /d "2050-01-01T00:00:00Z" /f',
            'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseUpdatesStartTime" /t REG_SZ /d "2023-07-07T09:59:52Z" /f',
            'reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseUpdatesExpiryTime" /t REG_SZ /d "2050-01-01T00:00:00Z" /f',
        ]
        execute_commands(commands)
        messagebox.showinfo("成功", "已成功暂停 Windows 自动更新")
    except Exception as e:
        messagebox.showerror("错误", f"暂停 Windows 自动更新失败: {e}")

# 取消暂停 Windows 自动更新
def un_disable_windows_update():
    try:
        commands = [
            'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "FlightSettingsMaxPauseDays" /f',
            'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseFeatureUpdatesStartTime" /f',
            'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseFeatureUpdatesEndTime" /f',
            'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseQualityUpdatesStartTime" /f',
            'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseQualityUpdatesEndTime" /f',
            'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseUpdatesStartTime" /f',
            'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v "PauseUpdatesExpiryTime" /f',
        ]
        execute_commands(commands)
        messagebox.showinfo("成功", "已成功取消暂停 Windows 自动更新")
    except Exception as e:
        messagebox.showerror("错误", f"取消暂停 Windows 自动更新失败: {e}")

# 禁用 Windows OneDrive
def disable_windows_onedrive():
    try:
        write_registry("HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\OneDrive", "DisableFileSyncNGSC", 1)
        messagebox.showinfo("成功", "已成功禁用 Windows OneDrive")
    except Exception as e:
        messagebox.showerror("错误", f"禁用 Windows OneDrive 失败: {e}")

# 启用 Windows OneDrive
def un_disable_windows_onedrive():
    try:
        write_registry("HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\OneDrive", "DisableFileSyncNGSC", 0)
        messagebox.showinfo("成功", "已成功启用 Windows OneDrive")
    except Exception as e:
        messagebox.showerror("错误", f"启用 Windows OneDrive 失败: {e}")
        
# 写入注册表
def write_registry(path, value_name, value):
    command = f'reg add "{path}" /v "{value_name}" /t REG_DWORD /d {value} /f'
    execute_commands([command])

# 执行注册表命令
def execute_commands(commands):
    if not is_admin():
        # 以管理员身份重新运行脚本
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return
    
    for cmd in commands:
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"成功执行: {cmd}")
        except subprocess.CalledProcessError as e:
            print(f"执行失败: {cmd}\n错误信息: {e}")

# 打开 GitHub 链接
def open_github():
    """打开 GitHub 链接"""
    webbrowser.open("https://github.com/WavesMan/Disable-automatic-Windows-update")

# 将窗口居中显示
def center_window(window, width, height):
    """将窗口居中显示"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

# 显示工具界面
def show_tools_frame():
    """显示工具界面"""
    about_frame.pack_forget()
    tools_frame.pack(fill=tk.BOTH, expand=True)

# 显示关于界面
def show_about_frame():
    """显示关于界面"""
    tools_frame.pack_forget()
    about_frame.pack(fill=tk.BOTH, expand=True)

# 从 GitHub 仓库获取最新版本信息（仅筛选 EXE 前缀的 tags）
def get_latest_version():
    """从 GitHub 仓库获取最新版本信息（仅筛选 EXE 前缀的 tags）"""
    try:
        # 调用 GitHub API 获取所有 releases
        response = requests.get("https://api.github.com/repos/WavesMan/Disable-automatic-Windows-update/releases")
        if response.status_code == 200:
            releases = response.json()
            # 筛选出 tags 前缀为 EXE 的 releases
            exe_releases = [release for release in releases if release["tag_name"].startswith("EXE-")]
            if exe_releases:
                # 获取最新的 EXE 版本
                latest_exe_version = exe_releases[0]["tag_name"]
                latest_version_label.config(text=f"最新版本: {latest_exe_version}")
            else:
                latest_version_label.config(text="未找到 EXE 前缀的版本")
        else:
            latest_version_label.config(text="无法获取版本信息")
    except Exception as e:
        latest_version_label.config(text=f"获取最新版本失败: {e}")

# 鼠标悬停时高亮背景
def on_enter(event, widget=None):
    """鼠标悬停时高亮背景"""
    target = widget if widget else event.widget
    target.config(background="#f0f0f0")
    sync_background_color(target, "#f0f0f0")

# 鼠标离开时恢复背景
def on_leave(event, widget=None):
    """鼠标离开时恢复背景"""
    target = widget if widget else event.widget
    target.config(background="white")
    sync_background_color(target, "white")

# 确保子控件的背景颜色与父容器同步
def sync_background_color(frame, color):
    """同步父容器和子控件的背景颜色"""
    for child in frame.winfo_children():
        child.config(bg=color)

# 导出日志文件
def export_logs():
    """导出日志文件"""
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    log_file = os.path.join(logs_dir, "app.log")
    
    if not os.path.exists(log_file):
        messagebox.showwarning("警告", "未找到日志文件！")
        logging.warning("未找到日志文件")
        return
    
    # 选择保存路径
    save_path = filedialog.asksaveasfilename(
        defaultextension=".log",
        filetypes=[("日志文件", "*.log")],
        title="保存日志文件"
    )
    
    if save_path:
        try:
            shutil.copy(log_file, save_path)
            messagebox.showinfo("成功", f"日志文件已导出到：{save_path}")
            logging.info(f"日志文件已导出到：{save_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出日志文件失败：{e}")
            logging.error(f"导出日志文件失败：{e}")
            logging.exception("异常堆栈信息")  # 记录异常堆栈

# 创建 GUI 界面
def create_gui():
    """创建 GUI 界面"""
    setup_logging()  # 初始化日志记录
    global tools_frame, about_frame, latest_version_label

    # 创建主窗口
    root = tk.Tk()
    root.title("Windows 自动更新管理")

    # 设置窗口大小
    window_width = 550
    window_height = 450
    root.geometry(f"{window_width}x{window_height}")

    # 将窗口居中显示
    center_window(root, window_width, window_height)

    # 设置窗口图标
    try:
        # 如果是打包后的环境，使用 sys._MEIPASS 获取资源路径
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 构建图标文件的完整路径
        icon_path = os.path.join(base_path, "windows.ico")
        root.iconbitmap(icon_path)
    except tk.TclError as e:
        print(f"无法加载图标文件: {e}")

    # 设置主题
    style = ttk.Style()
    style.theme_use("vista")  # 使用 Windows 主题

    # 动态检测系统主题并设置颜色
    if darkdetect.isDark():
        sidebar_color = "#2d2d2d"  # 深色模式侧边栏颜色
        button_color = sidebar_color
        text_color = "#ffffff"  # 白色文字
    else:
        sidebar_color = "#e1f5fe"  # 浅色模式侧边栏颜色
        button_color = sidebar_color
        text_color = "#000000"  # 黑色文字

    ###########################################################################################################
    # 创建侧边栏
    ###########################################################################################################
    sidebar = tk.Frame(root, bg=sidebar_color, width=120)
    sidebar.pack(side=tk.LEFT, fill=tk.Y)

    # 添加侧边栏按钮
    tools_button = tk.Button(
        sidebar,
        text="工具",
        font=("Microsoft YaHei", 12),
        bg=button_color,
        fg=text_color,
        activebackground=button_color,  # 悬停时背景色不变
        activeforeground="#005bb5",  # 悬停时文字颜色变为深蓝色
        bd=0,  # 去掉边框
        relief=tk.FLAT,  # 扁平样式
        cursor="hand2",  # 鼠标悬停时显示手型
        command=show_tools_frame,
    )
    tools_button.pack(pady=10, padx=10, fill=tk.X)

    about_button = tk.Button(
        sidebar,
        text="关于",
        font=("Microsoft YaHei", 12),
        bg=button_color,
        fg=text_color,
        activebackground=button_color,
        activeforeground="#005bb5",  # 悬停时文字颜色变为深蓝色
        bd=0,
        relief=tk.FLAT,
        cursor="hand2",
        command=show_about_frame,
    )
    about_button.pack(pady=10, padx=10, fill=tk.X)

    ###########################################################################################################
    # 创建工具界面
    ###########################################################################################################
    tools_frame = ttk.Frame(root)

    ###########################################################################################################
    # Windows 更新管理
    ###########################################################################################################
    update_label = ttk.Label(tools_frame, text="暂停 Windows 自动更新", font=("Microsoft YaHei", 14))
    update_label.pack(pady=10)

    update_button_frame = ttk.Frame(tools_frame)
    update_button_frame.pack()

    pause_update_button = ttk.Button(
        update_button_frame,
        text="暂停更新",
        style="TButton",
        command=disable_windows_update,
    )
    pause_update_button.pack(side=tk.LEFT, padx=10, pady=10)

    unpause_update_button = ttk.Button(
        update_button_frame,
        text="取消暂停更新",
        style="TButton",
        command=un_disable_windows_update,
    )
    unpause_update_button.pack(side=tk.LEFT, padx=10, pady=10)

    ###########################################################################################################
    # Windows Defender 管理
    ###########################################################################################################
    defender_label = ttk.Label(tools_frame, text="禁用 Windows Defender", font=("Microsoft YaHei", 14))
    defender_label.pack(pady=10)

    defender_button_frame = ttk.Frame(tools_frame)
    defender_button_frame.pack()

    disable_defender_button = ttk.Button(
        defender_button_frame,
        text="禁用",
        style="TButton",
        command=disable_defender,
    )
    disable_defender_button.pack(side=tk.LEFT, padx=10, pady=10)

    enable_defender_button = ttk.Button(
        defender_button_frame,
        text="取消禁用",
        style="TButton",
        command=un_disable_defender,
    )
    enable_defender_button.pack(side=tk.LEFT, padx=10, pady=10)

    ###########################################################################################################
    # Windows OneDrive 管理
    ###########################################################################################################
    onedrive_label = ttk.Label(tools_frame, text="禁用 Windows OneDrive", font=("Microsoft YaHei", 14))
    onedrive_label.pack(pady=10)

    onedrive_button_frame = ttk.Frame(tools_frame)
    onedrive_button_frame.pack()

    disable_onedrive_button = ttk.Button(
        onedrive_button_frame,
        text="禁用",
        style="TButton",
        command=disable_windows_onedrive,
    )
    disable_onedrive_button.pack(side=tk.LEFT, padx=10, pady=10)

    enable_onedrive_button = ttk.Button(
        onedrive_button_frame,
        text="取消禁用",
        style="TButton",
        command=un_disable_windows_onedrive,
    )
    enable_onedrive_button.pack(side=tk.LEFT, padx=10, pady=10)

    ###########################################################################################################
    # 创建关于界面
    ###########################################################################################################
    about_frame = ttk.Frame(root)
    about_label = ttk.Label(
        about_frame,
        text="关于本应用程序",
        font=("Microsoft YaHei", 14),
        anchor="w",  # 文字左对齐
    )
    about_label.pack(pady=20, padx=20, fill=tk.X)

    ###########################################################################################################
    # 第一栏：当前程序版本
    ###########################################################################################################
    version_label = tk.Label(
        about_frame,
        text="当前程序版本: v1.6",
        font=("Microsoft YaHei", 12),
        bg="white",
        anchor="w",  # 文字左对齐
        height=2,  # 增加高度
    )
    version_label.pack(pady=5, padx=20, fill=tk.X, ipady=5)  # 增加内部填充
    version_label.bind("<Enter>", lambda event: on_enter(event, version_label))
    version_label.bind("<Leave>", lambda event: on_leave(event, version_label))

    ###########################################################################################################
    # 第二栏：开发者信息
    ###########################################################################################################
    developer_label = tk.Label(
        about_frame,
        text="开发者: WavesMan",
        font=("Microsoft YaHei", 12),
        bg="white",
        anchor="w",  # 文字左对齐
        height=2,  # 增加高度
    )
    developer_label.pack(pady=5, padx=20, fill=tk.X, ipady=5)  # 增加内部填充
    developer_label.bind("<Enter>", lambda event: on_enter(event, developer_label))
    developer_label.bind("<Leave>", lambda event: on_leave(event, developer_label))

    ###########################################################################################################
    # 第三栏：仓库地址（可点击）
    ###########################################################################################################
    repo_frame = tk.Frame(about_frame, bg="white")  # 创建一个 Frame 容器
    repo_frame.pack(pady=5, padx=20, fill=tk.X, ipady=5)  # 增加内部填充

    # 第一行：仓库地址
    repo_text_label = tk.Label(
        repo_frame,
        text="仓库地址:",
        font=("Microsoft YaHei", 10),
        fg="black",  # 文字颜色为黑色
        bg="white",  # 背景颜色与父容器一致
        anchor="w",  # 文字左对齐
    )
    repo_text_label.pack(fill=tk.X)  # 左对齐并填充宽度

    # 第二行：链接
    repo_link_label = tk.Label(
        repo_frame,
        text="https://github.com/WavesMan/Disable-automatic-Windows-update",
        font=("Microsoft YaHei", 10),
        bg="white",  # 背景颜色与父容器一致
        cursor="hand2",  # 鼠标悬停时显示手型
        anchor="w",  # 文字左对齐
    )
    repo_link_label.pack(fill=tk.X)  # 左对齐并填充宽度

    # 绑定点击事件
    repo_link_label.bind("<Button-1>", lambda event: open_github())

    # 绑定鼠标悬停事件到父容器
    repo_frame.bind("<Enter>", lambda event: on_enter(event, repo_frame))
    repo_frame.bind("<Leave>", lambda event: on_leave(event, repo_frame))

    ###########################################################################################################
    # 第四栏：获取最新版本
    ###########################################################################################################
    latest_version_label = tk.Label(
        about_frame,
        text="点击此处获取最新版本",
        font=("Microsoft YaHei", 12),
        bg="white",
        cursor="hand2",
        anchor="w",  # 文字左对齐
        height=2,  # 增加高度
    )
    latest_version_label.pack(pady=5, padx=20, fill=tk.X, ipady=5)  # 增加内部填充
    latest_version_label.bind("<Enter>", lambda event: on_enter(event, latest_version_label))
    latest_version_label.bind("<Leave>", lambda event: on_leave(event, latest_version_label))
    latest_version_label.bind("<Button-1>", lambda event: get_latest_version())

    ###########################################################################################################
    # 第五栏：导出日志
    ###########################################################################################################
    export_logs_label = tk.Label(
        about_frame,
        text="导出运行日志",
        font=("Microsoft YaHei", 12),
        bg="white",
        cursor="hand2",
        anchor="w",  # 文字左对齐
        height=2,  # 增加高度
    )
    export_logs_label.pack(pady=5, padx=20, fill=tk.X, ipady=5)  # 增加内部填充
    export_logs_label.bind("<Enter>", lambda event: on_enter(event, export_logs_label))
    export_logs_label.bind("<Leave>", lambda event: on_leave(event, export_logs_label))
    export_logs_label.bind("<Button-1>", lambda event: export_logs())

    ###########################################################################################################
    # 默认显示工具界面
    ###########################################################################################################
    show_tools_frame()

    ###########################################################################################################
    # 添加页脚文字
    ###########################################################################################################
    footer_label = ttk.Label(
        root,
        text="Powered by GitHub@WavesMan",
        font=("Microsoft YaHei", 10),
        foreground="gray",
        cursor="hand2",
    )
    footer_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    # 绑定点击事件
    footer_label.bind("<Button-1>", lambda event: open_github())

    ###########################################################################################################
    # 运行主循环
    ###########################################################################################################
    root.mainloop()

if __name__ == "__main__":
    setup_logging()  # 配置日志记录
    create_gui()