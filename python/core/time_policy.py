from datetime import datetime, timezone, timedelta


def to_local_dt(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    """
    将数值形式的年月日时分构造成本地时区的 datetime

    参数约束：
    - 年份范围建议为 2000-2100（UI 已限制），月份 1-12，日期 1-31，小时 0-23，分钟 0-59
    - 非法值将由调用方捕获异常后进行提示

    返回：
    - 本地时区标注的 datetime（带 tzinfo）
    """
    dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
    tz = datetime.now().astimezone().tzinfo
    return dt.replace(tzinfo=tz)


def to_utc_iso(dt: datetime) -> str:
    """
    将 datetime 转换为 ISO8601 UTC 字符串（形如 2026-02-07T09:00:00Z）

    逻辑说明：
    - 统一写入注册表使用 UTC，避免本地时区/夏令时变更导致的偏差
    - 显示层按本地时区呈现即可
    """
    u = dt.astimezone(timezone.utc)
    return u.strftime("%Y-%m-%dT%H:%M:%SZ")


def clamp_pause_window(start: datetime, end: datetime, max_allowed_days: int = 35) -> tuple[int, datetime]:
    """
    计算并约束暂停窗口，返回（max_days, 调整后的结束时间）

    规则：
    - 结束时间必须晚于开始时间；否则由调用方提示错误
    - 天数取向上取整（不足 1 天按 1 天处理），确保覆盖整天策略
    - 超过系统允许最大天数时，结束时间按允许上限截断

    返回：
    - max_days：用于写入 FlightSettingsMaxPauseDays 的整数天数
    - end_adj：若超出上限则截断后的结束时间，否则为原值
    """
    diff_sec = (end - start).total_seconds()
    days = int(diff_sec // 86400)
    if diff_sec % 86400:
        days += 1
    if days < 1:
        days = 1
    if days > max_allowed_days:
        days = max_allowed_days
        end = start + timedelta(days=max_allowed_days)
    return days, end


def compute_pause_params(
    start: datetime,
    preset_days: int | None,
    custom_end: datetime | None,
    max_allowed_days: int = 35,
    clamp: bool = True,
) -> tuple[int, str, str, datetime]:
    """
    生成暂停所需参数（max_days、start_iso、end_iso、本地结束时间）

    输入：
    - start：本地时区开始时间
    - preset_days：预设天数（7/14/35 等）；若为 None 则使用 custom_end
    - custom_end：自定义结束时间；若为 None 则根据 preset_days 计算
    - max_allowed_days：系统允许最大天数，默认 35

    输出：
    - max_days：写入 FlightSettingsMaxPauseDays 的整数天数
    - start_iso：UTC ISO8601 的开始时间
    - end_iso：UTC ISO8601 的结束时间（可能已按上限截断）
    - end_local：用于 UI 展示的本地结束时间（已与上限规则一致）
    """
    if preset_days is not None:
        end_dt = start + timedelta(days=int(preset_days))
    else:
        end_dt = custom_end  
    if clamp:
        max_days, end_adj = clamp_pause_window(start, end_dt, max_allowed_days)
    else:
        diff_sec = (end_dt - start).total_seconds()
        days = int(diff_sec // 86400)
        if diff_sec % 86400:
            days += 1
        if days < 1:
            days = 1
        max_days = days
        end_adj = end_dt
    s_iso = to_utc_iso(start)
    e_iso = to_utc_iso(end_adj)
    end_local = end_adj.astimezone(datetime.now().astimezone().tzinfo)
    return max_days, s_iso, e_iso, end_local
