import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser

from ..admin.service import is_admin, run_as_admin
from ..utils.logger import setup_logging
from ..core.main import (
    pause_updates,
    resume_updates,
    disable_defender,
    enable_defender,
    disable_onedrive,
    enable_onedrive,
    get_version,
    export_logs,
    check_update,
    disable_firewall,
    enable_firewall,
)

def gui():
    # NOTE: 界面初始化前完成日志初始化与权限校验；日志路径用于导出功能
    log_path = setup_logging()
    if not is_admin():
        messagebox.showinfo("提示", "需要管理员权限运行")
        run_as_admin()

    root = tk.Tk()
    root.title("Windows 更新管理")
    root.geometry("550x550")
    x, y = (root.winfo_screenwidth() - 550) // 2, (root.winfo_screenheight() - 550) // 2
    root.geometry(f"550x550+{x}+{y}")
    root.resizable(False, False)
    root.minsize(550, 550)
    root.maxsize(550, 550)
    ttk.Style().theme_use("vista")

    # NOTE: 单页简化界面：顶部操作区 + 两个功能区（更新、Defender）
    topbar = ttk.Frame(root)
    topbar.pack(fill=tk.X, padx=10, pady=10)
    ttk.Button(topbar, text="检查更新", command=_check_update).pack(side=tk.RIGHT)
    ttk.Button(topbar, text="导出日志", command=lambda: _export_logs(log_path)).pack(side=tk.RIGHT, padx=10)

    content = ttk.Frame(root)
    content.pack(fill=tk.BOTH, expand=True)

    ttk.Label(content, text="暂停 Windows 更新", font=("Microsoft YaHei", 14)).pack(pady=10)
    f1 = ttk.Frame(content)
    f1.pack()
    create_btn(f1, "暂停", lambda: _handle_result(pause_updates(), "已暂停 Windows 更新"))
    create_btn(f1, "取消", lambda: _handle_result(resume_updates(), "已取消暂停更新"))

    ttk.Label(content, text="禁用 Windows Defender", font=("Microsoft YaHei", 14)).pack(pady=10)
    f2 = ttk.Frame(content)
    f2.pack()
    create_btn(f2, "禁用", lambda: _handle_result(disable_defender(), "已禁用 Defender"))
    create_btn(f2, "取消", lambda: _handle_result(enable_defender(), "已启用 Defender"))

    ttk.Label(content, text="停用 Windows 防火墙", font=("Microsoft YaHei", 14)).pack(pady=10)
    f_fw = ttk.Frame(content)
    f_fw.pack()
    create_btn(f_fw, "停用", lambda: _handle_result(disable_firewall(), "已停用防火墙"))
    create_btn(f_fw, "恢复", lambda: _handle_result(enable_firewall(), "已恢复防火墙"))

    ttk.Label(content, text="禁用 OneDrive", font=("Microsoft YaHei", 14)).pack(pady=10)
    f3 = ttk.Frame(content)
    f3.pack()
    create_btn(f3, "禁用", lambda: _handle_result(disable_onedrive(), "已禁用 OneDrive"))
    create_btn(f3, "取消", lambda: _handle_result(enable_onedrive(), "已启用 OneDrive"))

    footer = ttk.Label(root, text="Powered by GitHub@WavesMan", font=("Microsoft YaHei", 10),
                       foreground="gray", cursor="hand2")
    footer.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
    footer.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/WavesMan/Disable-automatic-Windows-update"))

    root.mainloop()


def _handle_result(result, success_msg: str):
    # NOTE: 统一成功/失败提示，保持 UI 一致性；错误信息从服务层透出但不暴露底层实现
    if result.ok:
        messagebox.showinfo("成功", success_msg)
    else:
        msg = result.error.get("message") if result.error else "操作失败"
        messagebox.showerror("错误", msg)


def create_btn(parent, text, command):
    btn = ttk.Button(parent, text=text, command=command)
    btn.pack(side=tk.LEFT, padx=10, pady=10)
    return btn


def _check_update():
    # NOTE: 仅提示有无新版本并引导到发布页，无关于页展示
    res = check_update()
    if res.ok and res.data:
        cur = res.data.get('current')
        latest = res.data.get('latest')
        if res.data.get('has_update'):
            if messagebox.askyesno("发现新版本", f"当前 {cur}，发现新版本 {latest}，是否前往发布页更新？"):
                webbrowser.open(res.data.get('release_url'))
        else:
            messagebox.showinfo("版本检查", f"当前 {cur} 已是最新版本")
    else:
        err = res.error.get("message") if res.error else "未知错误"
        messagebox.showerror("错误", err)


def _export_logs(log_path: str):
    save_path = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("日志文件", "*.log")])
    if not save_path:
        return
    res = export_logs(log_path, save_path)
    if res.ok and res.data:
        messagebox.showinfo("成功", f"日志已导出到：{save_path}")
    else:
        msg = res.error.get("message") if res.error else "导出失败"
        messagebox.showerror("错误", msg)
