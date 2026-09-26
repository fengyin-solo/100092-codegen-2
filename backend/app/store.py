"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.modules import MODULES, MODULE_DATE_FIELDS, MODULE_KEYS, MODULE_LABELS
from app.seed import SEED_ROWS

# 看板支持的统计区间：key -> 往回数的天数；"all" 表示不限区间。
RANGE_DAYS: dict[str, int | None] = {
    "today": 0,
    "7d": 7,
    "30d": 30,
    "all": None,
}
DEFAULT_RANGE = "30d"


def _parse_date(value: Any) -> date | None:
    """把记录里的日期文本解析成 date；占位文本或缺失值返回 None。"""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }

    def module_names(self) -> list[str]:
        # 以注册表为准，空模块（没有任何记录）也会出现在清单里。
        return list(MODULE_KEYS)

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def overview(self, range_key: str = DEFAULT_RANGE) -> dict[str, object]:
        """运营概览：按统计区间汇总各模块的新增、待处理与异常情况。

        - 新增量只统计记录时间落在区间内的记录；模块本身没有日期字段时，
          历史存量记录不按区间过滤，新增量留空（前端展示「暂无」）。
        - 待处理量与异常量属于当前存量：区间内有记录的日期字段模块按区间统计，
          无日期字段的模块按全量统计，避免区间一换这些模块全部消失。
        - 最近记录时间取区间内（不限区间时取全量）最大的记录日期，取不到为 None。
        """
        days = RANGE_DAYS.get(range_key, RANGE_DAYS[DEFAULT_RANGE])
        today = date.today()
        start = None if days is None else today - timedelta(days=days)

        modules: list[dict[str, object]] = []
        for key in MODULE_KEYS:
            rows = self.rows(key)
            date_field = MODULE_DATE_FIELDS[key]
            modules.append(self._summarize_module(key, rows, date_field, start))

        # 看板下钻统一按待处理量从高到低排列；没有数据的模块（None）沉底，
        # 待处理量相同时再按异常量、模块名兜底，保证切换区间后顺序随之变化且稳定。
        modules.sort(
            key=lambda item: (
                -(item["pending"] if item["pending"] is not None else -1),
                -(item["abnormal"] if item["abnormal"] is not None else -1),
                str(item["name"]),
            )
        )

        created_values = [int(item["created"]) for item in modules if item["created"] is not None]
        cards = [
            {"key": "modules", "label": "业务模块", "value": len(modules)},
            {
                "key": "created",
                "label": "区间新增",
                "value": sum(created_values),
            },
            {
                "key": "pending",
                "label": "待处理",
                "value": sum(int(item["pending"]) for item in modules if item["pending"] is not None),
            },
            {
                "key": "abnormal",
                "label": "异常量",
                "value": sum(int(item["abnormal"]) for item in modules if item["abnormal"] is not None),
            },
        ]
        return {"range": range_key, "cards": cards, "modules": modules}

    @staticmethod
    def _summarize_module(
        key: str,
        rows: list[dict[str, Any]],
        date_field: str | None,
        start: date | None,
    ) -> dict[str, object]:
        total = len(rows)
        base: dict[str, object] = {
            "key": key,
            "name": MODULE_LABELS[key],
            "path": f"/{key}",
            "total": total,
            "hasDateField": date_field is not None,
        }
        if not rows:
            # 空模块：各指标留空，由前端展示「暂无数据」而不是 0。
            return {**base, "created": None, "pending": None, "abnormal": None, "latestTime": None}

        if date_field is None:
            # 没有记录时间字段的存量模块：不参与区间新增统计，存量指标全量计算。
            return {
                **base,
                "created": None,
                "pending": sum(1 for row in rows if row.get("pending")),
                "abnormal": sum(1 for row in rows if row.get("abnormal")),
                "latestTime": None,
            }

        dated = [
            (row, parsed)
            for row in rows
            if (parsed := _parse_date(row.get(date_field))) is not None
        ]
        if start is not None:
            in_range = [(row, parsed) for row, parsed in dated if parsed >= start]
        else:
            in_range = dated

        if not in_range:
            # 区间内没有任何记录：指标留空，区别于区间内确有 0 条待处理。
            return {**base, "created": None, "pending": None, "abnormal": None, "latestTime": None}

        latest = max(parsed for _, parsed in in_range)
        return {
            **base,
            "created": len(in_range),
            "pending": sum(1 for row, _ in in_range if row.get("pending")),
            "abnormal": sum(1 for row, _ in in_range if row.get("abnormal")),
            "latestTime": latest.isoformat(),
        }


store = Store()
