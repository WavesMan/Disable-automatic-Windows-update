import tkinter as tk
import subprocess
import webbrowser

def run_script(script_name):
    """运行指定的 Python 脚本"""
    try:
        subprocess.run(["python", script_name], check=True)
        print(f"成功运行: {script_name}")
    except subprocess.CalledProcessError as e:
        print(f"运行失败: {script_name}\n错误信息: {e}")

def open_github():
    """打开 GitHub 链接"""
    webbrowser.open("https://github.com/WavesMan/Disable-automatic-Windows-update")

def center_window(window, width, height):
    """将窗口居中显示"""
    # 获取屏幕宽度和高度
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # 计算窗口的左上角坐标
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    # 设置窗口位置
    window.geometry(f"{width}x{height}+{x}+{y}")

def create_gui():
    """创建 GUI 界面"""
    # 创建主窗口
    root = tk.Tk()
    root.title("Windows 自动更新管理")

    # 设置窗口大小
    window_width = 400
    window_height = 150
    root.geometry(f"{window_width}x{window_height}")

    # 将窗口居中显示
    center_window(root, window_width, window_height)

    # 设置字体
    font_name = "Microsoft YaHei"  # 微软雅黑
    label_font = (font_name, 14)   # 标签字体
    button_font = (font_name, 12)  # 按钮字体
    footer_font = ("KaiTi", 10)    # 页脚字体（楷体，字号10）

    # 添加文字标签
    label = tk.Label(root, text="暂停Windows自动更新", font=label_font)
    label.pack(pady=20)  # 设置上下边距

    # 创建一个 Frame 容器，用于放置按钮
    button_frame = tk.Frame(root)
    button_frame.pack()

    # 添加“暂停更新”按钮
    pause_button = tk.Button(
        button_frame,
        text="暂停更新",
        font=button_font,
        width=15,  # 设置按钮宽度
        command=lambda: run_script("./_internal/disable-windows-update.py"),  # 点击后运行 01.py
    )
    pause_button.pack(side=tk.LEFT, padx=10)  # 左对齐，设置左右边距

    # 添加“取消暂停更新”按钮
    unpause_button = tk.Button(
        button_frame,
        text="取消暂停更新",
        font=button_font,
        width=15,  # 设置按钮宽度
        command=lambda: run_script("./_internal/un-disable-windows-update.py"),  # 点击后运行 02.py
    )
    unpause_button.pack(side=tk.LEFT, padx=10)  # 左对齐，设置左右边距

    # 添加页脚文字
    footer_label = tk.Label(
        root,
        text="Powered by GitHub@WavesMan",
        font=footer_font,
        fg="gray",  # 设置文字颜色为灰色
        cursor="hand2",  # 设置鼠标悬停样式为手型
    )
    # 将页脚文字放置在右下角
    footer_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)  # relx/rely 为相对位置，anchor 为锚点

    # 绑定点击事件
    footer_label.bind("<Button-1>", lambda event: open_github())

    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    create_gui()