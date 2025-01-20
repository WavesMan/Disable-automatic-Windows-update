import tkinter as tk
from tkinter import ttk
import os
import sys
import subprocess
import webbrowser
import darkdetect  # 用于检测系统主题
import requests  # 用于调用 GitHub API

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
        
        # 运行脚本
        subprocess.run(["python", script_path], check=True)
        print(f"成功运行: {script_name}")
    except subprocess.CalledProcessError as e:
        print(f"运行失败: {script_name}\n错误信息: {e}")

def open_github():
    """打开 GitHub 链接"""
    webbrowser.open("https://github.com/WavesMan/Disable-automatic-Windows-update")

def center_window(window, width, height):
    """将窗口居中显示"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def show_tools_frame():
    """显示工具界面"""
    about_frame.pack_forget()
    tools_frame.pack(fill=tk.BOTH, expand=True)

def show_about_frame():
    """显示关于界面"""
    tools_frame.pack_forget()
    about_frame.pack(fill=tk.BOTH, expand=True)

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

def on_enter(event, widget=None):
    """鼠标悬停时高亮背景"""
    target = widget if widget else event.widget
    target.config(background="#f0f0f0")

def on_leave(event, widget=None):
    """鼠标离开时恢复背景"""
    target = widget if widget else event.widget
    target.config(background="white")

def create_gui():
    """创建 GUI 界面"""
    global tools_frame, about_frame, latest_version_label

    # 创建主窗口
    root = tk.Tk()
    root.title("Windows 自动更新管理")

    # 设置窗口大小
    window_width = 550
    window_height = 400
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
        command=lambda: run_script("./_internal/disable-windows-update.py"),
    )
    pause_update_button.pack(side=tk.LEFT, padx=10, pady=10)

    unpause_update_button = ttk.Button(
        update_button_frame,
        text="取消暂停更新",
        style="TButton",
        command=lambda: run_script("./_internal/un-disable-windows-update.py"),
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
        command=lambda: run_script("./_internal/disable-windows-defender.py"),
    )
    disable_defender_button.pack(side=tk.LEFT, padx=10, pady=10)

    enable_defender_button = ttk.Button(
        defender_button_frame,
        text="取消禁用",
        style="TButton",
        command=lambda: run_script("./_internal/un-disable-windows-defender.py"),
    )
    enable_defender_button.pack(side=tk.LEFT, padx=10, pady=10)

    ###########################################################################################################
    # Windows OneDrive 管理
    ###########################################################################################################
    defender_label = ttk.Label(tools_frame, text="禁用Windows OneDrive", font=("Microsoft YaHei", 14))
    defender_label.pack(pady=10)

    defender_button_frame = ttk.Frame(tools_frame)
    defender_button_frame.pack()

    disable_defender_button = ttk.Button(
        defender_button_frame,
        text="禁用",
        style="TButton",
        command=lambda: run_script("./_internal/disable-Windows-OneDirve.py"),
    )
    disable_defender_button.pack(side=tk.LEFT, padx=10, pady=10)

    enable_defender_button = ttk.Button(
        defender_button_frame,
        text="取消禁用",
        style="TButton",
        command=lambda: run_script("./_internal/un-disable-Windows-OneDirve.py"),
    )
    enable_defender_button.pack(side=tk.LEFT, padx=10, pady=10)

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
        text="当前程序版本: v1.5",
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
    # 确保子控件的背景颜色与父容器同步
    ###########################################################################################################
    def sync_background_color(frame, color):
        """同步父容器和子控件的背景颜色"""
        for child in frame.winfo_children():
            child.config(bg=color)

    # 修改 on_enter 和 on_leave 函数以同步背景颜色
    def on_enter(event, widget=None):
        """鼠标悬停时高亮背景"""
        target = widget if widget else event.widget
        target.config(background="#f0f0f0")
        if widget:  # 如果是父容器，同步子控件的背景颜色
            sync_background_color(widget, "#f0f0f0")

    def on_leave(event, widget=None):
        """鼠标离开时恢复背景"""
        target = widget if widget else event.widget
        target.config(background="white")
        if widget:  # 如果是父容器，同步子控件的背景颜色
            sync_background_color(widget, "white")

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
    create_gui()