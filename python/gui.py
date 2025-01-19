import tkinter as tk
import subprocess

def run_script(script_name):
    """运行指定的 Python 脚本"""
    try:
        subprocess.run(["python", script_name], check=True)
        print(f"成功运行: {script_name}")
    except subprocess.CalledProcessError as e:
        print(f"运行失败: {script_name}\n错误信息: {e}")

def create_gui():
    """创建 GUI 界面"""
    # 创建主窗口
    root = tk.Tk()
    root.title("Windows 自动更新管理")
    root.geometry("400x150")  # 设置窗口大小

    # 设置字体
    font_name = "Microsoft YaHei"  # 微软雅黑
    label_font = (font_name, 14)   # 标签字体
    button_font = (font_name, 12)  # 按钮字体

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
        command=lambda: run_script("01.py"),  # 点击后运行 01.py
    )
    pause_button.pack(side=tk.LEFT, padx=10)  # 左对齐，设置左右边距

    # 添加“取消暂停更新”按钮
    unpause_button = tk.Button(
        button_frame,
        text="取消暂停更新",
        font=button_font,
        width=15,  # 设置按钮宽度
        command=lambda: run_script("02.py"),  # 点击后运行 02.py
    )
    unpause_button.pack(side=tk.LEFT, padx=10)  # 左对齐，设置左右边距

    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    create_gui()