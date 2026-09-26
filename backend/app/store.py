"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

from app.seed import SEED_ROWS

# 看板模块的键、中文名与排列顺序，必须和左侧导航保持一致
# （前端 src/modules.ts 同源维护，路由路径就是 /{key}）。
MODULE_META: list[tuple[str, str]] = [
    ("sample", "样品登记"),
    ("contract", "委托合同"),
    ("task", "检测任务"),
    ("method", "检测方法"),
    ("instrument", "仪器设备"),
    ("standard", "标准物质"),
    ("result", "检测结果"),
    ("report", "检测报告"),
    ("boundary", "分包检测"),
    ("abnormal", "不符合项"),
    ("envmonitor", "环境监控"),
    ("blind", "盲样考核"),
    ("ability", "能力验证"),
    ("intermediate", "中间液配制"),
    ("audit", "内审检查"),
    ("certification", "认证认可"),
    ("quality", "质控样"),
    ("reagent2", "试剂管理"),
    ("waste", "实验废液"),
    ("opinion", "客户反馈"),
]

# 每个模块用来判断“最近一条记录时间”的日期字段；
# 没有日期字段的模块（检测任务、检测方法等）按种子序号补一个时间。
DATE_FIELDS: dict[str, str | None] = {
    "sample": "采样日期",
    "contract": "签订日期",
    "task": None,
    "method": None,
    "instrument": "检定日期",
    "standard": "开封日期",
    "result": None,
    "report": "报告日期",
    "boundary": "送样日期",
    "abnormal": None,
    "envmonitor": "监测时间",
    "blind": "考核日期",
    "ability": "上报日期",
    "intermediate": "配制日期",
    "audit": "内审日期",
    "certification": "获证日期",
    "quality": "进库日期",
    "reagent2": None,
    "waste": "产生日期",
    "opinion": "反馈日期",
}

# 统计区间参数 -> 回看时长；today 单独按当天零点截断，all 不限制。
RANGE_CHOICES = ("today", "7d", "30d", "all")
_SEED_BASE_DATE = datetime(2026, 9, 1)


def _parse_datetime(value: Any) -> datetime | None:
    """尽量把记录里的日期字符串解析成时间；解析不了就返回 None。"""
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _format_record_time(value: str | None) -> str | None:
    """展示用：只有日期的记录不补 00:00，带具体时分的新记录保留时分。"""
    parsed = _parse_datetime(value)
    if parsed is None:
        return None
    if parsed.time() == time(0, 0):
        return parsed.strftime("%Y-%m-%d")
    return parsed.strftime("%Y-%m-%d %H:%M")


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            key: [dict(row) for row in SEED_ROWS.get(key, [])]
            for key, _ in MODULE_META
        }
        for key, table in self._tables.items():
            for ordinal, row in enumerate(table, start=1):
                if row.get("record_time"):
                    continue
                row["record_time"] = self._seed_record_time(key, row, ordinal)

    def _seed_record_time(self, module: str, row: dict[str, Any], ordinal: int) -> str:
        """种子行优先取模块自带的日期字段；没有日期字段时按序号铺一个 9 月上旬的时间。"""
        field = DATE_FIELDS.get(module)
        parsed = _parse_datetime(row.get(field)) if field else None
        if parsed is None:
            parsed = _SEED_BASE_DATE + timedelta(days=ordinal - 1)
        return parsed.strftime("%Y-%m-%d %H:%M:%S")

    def _stamp_new_row(self, module: str, row: dict[str, Any]) -> None:
        """运行期新建的行没有 record_time：有日期字段用日期，没有就记当前时间。"""
        field = DATE_FIELDS.get(module)
        parsed = _parse_datetime(row.get(field)) if field else None
        if parsed is None:
            parsed = datetime.now()
        row["record_time"] = parsed.strftime("%Y-%m-%d %H:%M:%S")

    def module_names(self) -> list[str]:
        return sorted(self._tables)

    def rows(self, module: str) -> list[dict[str, Any]]:
        table = self._tables.setdefault(module, [])
        # 兜住各业务服务直接 append 进来、忘了带 record_time 的新行。
        for row in table:
            if not row.get("record_time"):
                self._stamp_new_row(module, row)
        return table

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def _range_start(self, range_key: str, now: datetime) -> datetime | None:
        if range_key == "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if range_key == "7d":
            return now - timedelta(days=7)
        if range_key == "30d":
            return now - timedelta(days=30)
        return None

    def overview(self, range_key: str = "all") -> dict[str, object]:
        """运营概览：按统计区间汇总各模块的新增、待处理与异常量。

        卡片数字与下钻明细来自同一份计算结果，保证看板内外口径一致；
        模块没有记录（或区间内没有记录）时数量为 0、latest 为 None，
        由前端决定展示“暂无”而不是一律显示 0。
        """
        now = datetime.now()
        start = self._range_start(range_key, now)

        modules: list[dict[str, object]] = []
        for key, label in MODULE_META:
            rows = self.rows(key)
            if start is None:
                scoped = list(rows)
            else:
                scoped = [
                    row
                    for row in rows
                    if (_parse_datetime(row.get("record_time")) or now) >= start
                ]
            latest = max(
                (str(row.get("record_time") or "") for row in scoped),
                default=None,
            )
            modules.append({
                "key": key,
                "name": label,
                "created": len(scoped),
                "pending": sum(1 for row in scoped if row.get("pending")),
                "abnormal": sum(1 for row in scoped if row.get("abnormal")),
                "latest": _format_record_time(latest),
                # has_data 区分“模块整张表就是空的”和“区间内暂时没有记录”。
                "has_data": bool(rows),
            })

        cards = [
            {"key": "modules", "label": "业务模块", "value": len(modules)},
            {"key": "created", "label": "区间新增",
             "value": sum(int(item["created"]) for item in modules)},
            {"key": "pending", "label": "待处理",
             "value": sum(int(item["pending"]) for item in modules)},
            {"key": "abnormal", "label": "异常量",
             "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {"range": range_key, "cards": cards, "modules": modules}


store = Store()
