import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import webbrowser
import logging
import time
import traceback

from ..admin.service import is_admin, run_as_admin
from ..utils.logger import setup_logging, log_event, new_op_id, set_op_id, reset_op_id
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
    pause_updates_with_times,
)
from ..core.time_policy import compute_pause_params
from .components import TimeRangeSelector


def gui():
    # NOTE: 界面初始化前完成日志初始化与权限校验；日志路径用于导出功能
    log_path = setup_logging()
    log_event(logging.INFO, "ui_init", "GUI 初始化开始", action="gui_init", status="started")
    if not is_admin():
        log_event(logging.INFO, "ui_admin_required", "检测到非管理员权限，准备提权", action="gui_init", status="required")
        messagebox.showinfo("提示", "需要管理员权限运行")
        run_as_admin()

    root = tk.Tk()
    root.title("Windows 更新管理")
    try:
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "windows.ico")
        root.iconbitmap(icon_path)
    except Exception:
        pass
    root.geometry("550x550")
    x, y = (root.winfo_screenwidth() - 550) // 2, (root.winfo_screenheight() - 550) // 2
    root.geometry(f"550x550+{x}+{y}")
    root.resizable(False, False)
    root.minsize(550, 560)
    root.maxsize(550, 560)
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
    f1.pack(pady=4)

    selector = TimeRangeSelector(f1)
    selector.pack(pady=6)

    def _pause_with_selector():
        action = "pause_updates_with_times"
        op_id = new_op_id()
        token = set_op_id(op_id)
        started = time.perf_counter()
        log_event(logging.INFO, "ui_action_started", "用户点击暂停更新", action=action, status="started")
        try:
            sdt, preset_days, edt, is_custom = selector.get_values()
        except ValueError as e:
            log_event(
                logging.ERROR,
                "ui_action_validation_failed",
                f"暂停更新参数校验失败: {e}",
                action=action,
                status="failed",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            messagebox.showerror("错误", str(e))
            reset_op_id(token)
            return
        try:
            md, s_iso, e_iso, end_local = compute_pause_params(
                sdt,
                None if is_custom else int(preset_days),
                edt,
                35,
                clamp=not is_custom,
            )
            try:
                selector._apply_date("end", end_local.year, end_local.month, end_local.day)
            except Exception:
                pass
            res = pause_updates_with_times(md, s_iso, e_iso)
            duration_ms = int((time.perf_counter() - started) * 1000)
            if res.ok:
                _handle_result(res, f"已暂停至 {end_local.strftime('%Y-%m-%d %H:%M')}", action, duration_ms)
            else:
                _handle_result(res, "暂停失败", action, duration_ms)
        except Exception as e:
            duration_ms = int((time.perf_counter() - started) * 1000)
            log_event(
                logging.ERROR,
                "ui_action_exception",
                f"暂停更新流程异常: {e}",
                action=action,
                status="failed",
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback.format_exc(),
                exc_info=True,
            )
            messagebox.showerror("错误", str(e))
        finally:
            reset_op_id(token)

    btn_row = ttk.Frame(content)
    btn_row.pack(pady=6)
    create_btn(btn_row, "暂停", _pause_with_selector)
    create_btn(btn_row, "取消", lambda: _run_simple_action("resume_updates", resume_updates, "已取消暂停更新"))

    ttk.Label(content, text="禁用 Windows Defender", font=("Microsoft YaHei", 14)).pack(pady=10)
    f2 = ttk.Frame(content)
    f2.pack()
    create_btn(f2, "禁用", lambda: _run_simple_action("disable_defender", disable_defender, "已禁用 Defender"))
    create_btn(f2, "取消", lambda: _run_simple_action("enable_defender", enable_defender, "已启用 Defender"))

    ttk.Label(content, text="停用 Windows 防火墙", font=("Microsoft YaHei", 14)).pack(pady=10)
    f_fw = ttk.Frame(content)
    f_fw.pack()
    create_btn(f_fw, "停用", lambda: _run_simple_action("disable_firewall", disable_firewall, "已停用防火墙"))
    create_btn(f_fw, "恢复", lambda: _run_simple_action("enable_firewall", enable_firewall, "已恢复防火墙"))

    ttk.Label(content, text="禁用 OneDrive", font=("Microsoft YaHei", 14)).pack(pady=10)
    f3 = ttk.Frame(content)
    f3.pack()
    create_btn(f3, "禁用", lambda: _run_simple_action("disable_onedrive", disable_onedrive, "已禁用 OneDrive"))
    create_btn(f3, "取消", lambda: _run_simple_action("enable_onedrive", enable_onedrive, "已启用 OneDrive"))

    footer = ttk.Label(root, text="Powered by GitHub@WavesMan", font=("Microsoft YaHei", 10),
                       foreground="gray", cursor="hand2")
    footer.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
    footer.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/WavesMan/Disable-automatic-Windows-update"))

    log_event(logging.INFO, "ui_ready", "GUI 初始化完成，进入事件循环", action="gui_init", status="ok")
    root.mainloop()


def _run_simple_action(action: str, invoke, success_msg: str):
    op_id = new_op_id()
    token = set_op_id(op_id)
    started = time.perf_counter()
    log_event(logging.INFO, "ui_action_started", f"用户触发操作: {action}", action=action, status="started")
    try:
        res = invoke()
        duration_ms = int((time.perf_counter() - started) * 1000)
        _handle_result(res, success_msg, action, duration_ms)
    except Exception as e:
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logging.ERROR,
            "ui_action_exception",
            f"界面操作异常: {e}",
            action=action,
            status="failed",
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc(),
            exc_info=True,
        )
        messagebox.showerror("错误", str(e))
    finally:
        reset_op_id(token)


def _handle_result(result, success_msg: str, action: str = "ui_action", duration_ms: int | None = None):
    # NOTE: 统一成功/失败提示，保持 UI 一致性；错误信息从服务层透出但不暴露底层实现
    if result.ok:
        log_event(logging.INFO, "ui_action_finished", success_msg, action=action, status="ok", duration_ms=duration_ms)
        messagebox.showinfo("成功", success_msg)
    else:
        msg = result.error.get("message") if result.error else "操作失败"
        log_event(
            logging.ERROR,
            "ui_action_finished",
            msg,
            action=action,
            status="failed",
            duration_ms=duration_ms,
            error_type=(result.error or {}).get("code", "UI_ACTION_FAILED"),
            error_message=msg,
        )
        messagebox.showerror("错误", msg)


def create_btn(parent, text, command):
    btn = ttk.Button(parent, text=text, command=command)
    btn.pack(side=tk.LEFT, padx=10, pady=10)
    return btn


def _check_update():
    # NOTE: 仅提示有无新版本并引导到发布页，无关于页展示
    action = "check_update"
    op_id = new_op_id()
    token = set_op_id(op_id)
    started = time.perf_counter()
    log_event(logging.INFO, "ui_action_started", "用户点击检查更新", action=action, status="started")
    try:
        res = check_update()
        duration_ms = int((time.perf_counter() - started) * 1000)
        if res.ok and res.data:
            cur = res.data.get('current')
            latest = res.data.get('latest')
            if res.data.get('has_update'):
                log_event(logging.INFO, "ui_check_update_result", f"发现新版本: {latest}", action=action, status="ok", duration_ms=duration_ms)
                if messagebox.askyesno("发现新版本", f"当前 {cur}，发现新版本 {latest}，是否前往发布页更新？"):
                    webbrowser.open(res.data.get('release_url'))
                    log_event(logging.INFO, "ui_check_update_open_release", "用户选择打开发布页", action=action, status="ok")
                else:
                    log_event(logging.INFO, "ui_check_update_open_release", "用户取消打开发布页", action=action, status="cancel")
            else:
                log_event(logging.INFO, "ui_check_update_result", "当前版本已最新", action=action, status="ok", duration_ms=duration_ms)
                messagebox.showinfo("版本检查", f"当前 {cur} 已是最新版本")
        else:
            err = res.error.get("message") if res.error else "未知错误"
            log_event(
                logging.ERROR,
                "ui_action_finished",
                f"检查更新失败: {err}",
                action=action,
                status="failed",
                duration_ms=duration_ms,
                error_type=(res.error or {}).get("code", "CHECK_UPDATE_FAILED"),
                error_message=err,
            )
            messagebox.showerror("错误", err)
    except Exception as e:
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logging.ERROR,
            "ui_action_exception",
            f"检查更新异常: {e}",
            action=action,
            status="failed",
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc(),
            exc_info=True,
        )
        messagebox.showerror("错误", str(e))
    finally:
        reset_op_id(token)


def _export_logs(log_path: str):
    action = "export_logs"
    op_id = new_op_id()
    token = set_op_id(op_id)
    started = time.perf_counter()
    log_event(logging.INFO, "ui_action_started", "用户点击导出日志", action=action, status="started")
    save_path = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("日志文件", "*.log")])
    if not save_path:
        log_event(logging.INFO, "ui_action_finished", "用户取消导出日志", action=action, status="cancel")
        reset_op_id(token)
        return
    try:
        res = export_logs(log_path, save_path)
        duration_ms = int((time.perf_counter() - started) * 1000)
        if res.ok and res.data:
            log_event(logging.INFO, "ui_action_finished", f"日志已导出到：{save_path}", action=action, status="ok", duration_ms=duration_ms)
            messagebox.showinfo("成功", f"日志已导出到：{save_path}")
        else:
            msg = res.error.get("message") if res.error else "导出失败"
            log_event(
                logging.ERROR,
                "ui_action_finished",
                msg,
                action=action,
                status="failed",
                duration_ms=duration_ms,
                error_type=(res.error or {}).get("code", "EXPORT_LOGS_FAILED"),
                error_message=msg,
            )
            messagebox.showerror("错误", msg)
    except Exception as e:
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logging.ERROR,
            "ui_action_exception",
            f"导出日志异常: {e}",
            action=action,
            status="failed",
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc(),
            exc_info=True,
        )
        messagebox.showerror("错误", str(e))
    finally:
        reset_op_id(token)
