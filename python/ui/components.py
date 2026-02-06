import tkinter as tk
from tkinter import ttk
from datetime import datetime, date
import calendar
import os


class TimeRangeSelector(ttk.Frame):
    """
    时间范围选择组件：删除旧的年月日 Spinbox，统一使用日历弹窗选择日期；保留时分选择。

    输入采集：开始日期+时分、结束预设或自定义日期+时分。
    """

    def __init__(self, master: tk.Misc):
        super().__init__(master)

        now = datetime.now()

        ttk.Label(self, text="开始时间").grid(row=0, column=0, padx=5, pady=6, sticky="w")
        self._start_y, self._start_m, self._start_d = now.year, now.month, now.day
        self.start_date_str = tk.StringVar(value=f"{self._start_y}-{self._start_m:02d}-{self._start_d:02d}")
        ttk.Label(self, textvariable=self.start_date_str, width=12).grid(row=0, column=1, padx=2)
        s_pick = ttk.Button(self, text="选择日期")
        s_pick.grid(row=0, column=3, padx=8)

        ttk.Label(self, text="结束时间").grid(row=1, column=0, padx=5, pady=6, sticky="w")
        self.preset_var = tk.StringVar(value="35")
        preset = ttk.Combobox(self, textvariable=self.preset_var, values=["7", "14", "35", "自定义"], width=6, state="readonly")
        preset.grid(row=1, column=1, padx=2)

        self._end_y, self._end_m, self._end_d = now.year, now.month, now.day
        self.end_date_str = tk.StringVar(value=f"{self._end_y}-{self._end_m:02d}-{self._end_d:02d}")
        self.end_date_label = ttk.Label(self, textvariable=self.end_date_str, width=12)
        self.end_date_label.grid(row=1, column=2, padx=2)
        e_pick = ttk.Button(self, text="选择日期", state="disabled")
        e_pick.grid(row=1, column=3, padx=8)

        def _toggle_end_fields(event=None):
            v = self.preset_var.get()
            st = "normal" if v == "自定义" else "disabled"
            e_pick.config(state=("normal" if v == "自定义" else "disabled"))

        preset.bind("<<ComboboxSelected>>", _toggle_end_fields)

        def _open_calendar(target: str):
            cal = CalendarPopup(self)
            limit_max = date(3000, 12, 31)
            if target == "start":
                y, m, d = self._start_y, self._start_m, self._start_d
                min_d = datetime.now().date()
                max_d = limit_max
            else:
                y, m, d = self._end_y, self._end_m, self._end_d
                min_d = date(self._start_y, self._start_m, self._start_d)
                max_d = limit_max
            cal.show(y, m, d, lambda yy, mm, dd: self._apply_date(target, yy, mm, dd), min_date=min_d, max_date=max_d)

        s_pick.config(command=lambda: _open_calendar("start"))
        e_pick.config(command=lambda: _open_calendar("end"))

    def _apply_date(self, target: str, y: int, m: int, d: int):
        if target == "start":
            self._start_y, self._start_m, self._start_d = y, m, d
            self.start_date_str.set(f"{y}-{m:02d}-{d:02d}")
        else:
            self._end_y, self._end_m, self._end_d = y, m, d
            self.end_date_str.set(f"{y}-{m:02d}-{d:02d}")

    def get_values(self):
        """
        读取用户选择并返回：
        - start_dt：datetime（本地时区，带 tzinfo）
        - preset_days：int 或 None（当选择预设时有效）
        - end_dt：datetime 或 None（当选择自定义时有效）
        - is_custom：bool（是否选择自定义结束时间）

        异常：
        - 当输入无法转换或超出 Spinbox 约束时抛出 ValueError，由上层处理提示
        """
        try:
            tz = datetime.now().astimezone().tzinfo
            start_dt = datetime(int(self._start_y), int(self._start_m), int(self._start_d), 0, 0, tzinfo=tz)
        except Exception as e:
            raise ValueError("开始时间非法") from e

        v = self.preset_var.get()
        if v == "自定义":
            try:
                end_dt = datetime(int(self._end_y), int(self._end_m), int(self._end_d), 23, 59, tzinfo=tz)
            except Exception as e:
                raise ValueError("结束时间非法") from e
            return start_dt, None, end_dt, True
        else:
            try:
                days = int(v)
            except Exception as e:
                raise ValueError("预设天数非法") from e
            return start_dt, days, None, False


class CalendarPopup(tk.Toplevel):
    """
    日历弹窗：支持年/月快速选择与无闪烁刷新；不引入第三方依赖。
    """

    def __init__(self, master: tk.Misc):
        super().__init__(master)
        self.title("选择日期")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self._y = None
        self._m = None
        self._d = None
        self._on_pick = None
        self._min_date: date | None = None
        self._max_date: date | None = None

        self.body = ttk.Frame(self)
        self.body.pack(padx=10, pady=10)

        header = ttk.Frame(self.body)
        header.pack(fill=tk.X)
        ttk.Button(header, text="<", width=3, command=self._prev_month).pack(side=tk.LEFT)
        self.year_var = tk.IntVar()
        self.month_var = tk.IntVar()
        self._y_box = ttk.Combobox(header, width=6, state="readonly", textvariable=self.year_var)
        self._m_box = ttk.Combobox(header, width=4, state="readonly", values=[str(m) for m in range(1, 13)], textvariable=self.month_var)
        self._y_box.pack(side=tk.LEFT, padx=6)
        ttk.Label(header, text="年").pack(side=tk.LEFT)
        self._m_box.pack(side=tk.LEFT, padx=6)
        ttk.Label(header, text="月").pack(side=tk.LEFT)
        ttk.Button(header, text=">", width=3, command=self._next_month).pack(side=tk.LEFT)

        grid = ttk.Frame(self.body)
        grid.pack(pady=6)
        for i, wd in enumerate(["一","二","三","四","五","六","日"]):
            ttk.Label(grid, text=wd).grid(row=0, column=i, padx=4, pady=2)
        self._day_btns = []
        for r in range(1, 7):
            row_btns = []
            for c in range(7):
                btn = ttk.Button(grid, text="", width=3)
                btn.grid(row=r, column=c, padx=2, pady=2)
                row_btns.append(btn)
            self._day_btns.append(row_btns)

        def _on_year_month_change(event=None):
            self._y = int(self.year_var.get())
            self._m = int(self.month_var.get())
            self._update_grid()

        self._y_box.bind("<<ComboboxSelected>>", _on_year_month_change)
        self._m_box.bind("<<ComboboxSelected>>", _on_year_month_change)

    def show(self, year: int, month: int, day: int, on_pick, min_date: date | None = None, max_date: date | None = None):
        self._y, self._m, self._d = int(year), int(month), int(day)
        self._on_pick = on_pick
        self._min_date = (min_date or date.min)
        self._max_date = (max_date or date.max)
        years = [str(y) for y in range(self._min_date.year, self._max_date.year + 1)]
        self._y_box.config(values=years)
        self.year_var.set(self._y)
        self.month_var.set(self._m)
        self._update_grid()
        self.update_idletasks()
        m = self.master.winfo_toplevel()
        x = m.winfo_rootx() + (m.winfo_width() - self.winfo_reqwidth()) // 2
        y = m.winfo_rooty() + 80
        self.geometry(f"+{x}+{y}")
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "windows.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass
        self.wait_window(self)

    def _update_grid(self):
        month_days = calendar.monthcalendar(self._y, self._m)
        for r in range(6):
            week = month_days[r] if r < len(month_days) else [0]*7
            for c in range(7):
                day = week[c]
                btn = self._day_btns[r][c]
                if day == 0:
                    btn.config(text="", state="disabled", command=lambda: None)
                else:
                    cur = date(self._y, self._m, day)
                    if cur < self._min_date or cur > self._max_date:
                        btn.config(text=str(day), state="disabled", command=lambda: None)
                    else:
                        btn.config(text=str(day), state="normal", command=lambda dd=day: self._pick(dd))

    def _prev_month(self):
        cand_m = self._m - 1
        cand_y = self._y
        if cand_m < 1:
            cand_m = 12
            cand_y -= 1
        first = date(cand_y, cand_m, 1)
        last_day = calendar.monthrange(cand_y, cand_m)[1]
        last = date(cand_y, cand_m, last_day)
        if last >= self._min_date:
            self._m, self._y = cand_m, cand_y
            self.year_var.set(self._y)
            self.month_var.set(self._m)
            self._update_grid()

    def _next_month(self):
        cand_m = self._m + 1
        cand_y = self._y
        if cand_m > 12:
            cand_m = 1
            cand_y += 1
        first = date(cand_y, cand_m, 1)
        if first <= self._max_date:
            self._m, self._y = cand_m, cand_y
            self.year_var.set(self._y)
            self.month_var.set(self._m)
            self._update_grid()

    def _pick(self, day: int):
        self._d = int(day)
        if self._on_pick:
            self._on_pick(self._y, self._m, self._d)
        self.destroy()
