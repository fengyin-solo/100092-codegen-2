"""业务模块注册表：运营概览看板与左侧导航共用同一份模块清单。

顺序、标签与前端左侧导航保持一致，保证看板里出现的每个模块都能对上导航入口；
date_field 指向该模块代表「记录产生时间」的字段，没有日期字段的模块记为 None，
这类历史存量记录不参与按区间过滤的新增量统计，但仍计入待处理量与异常量。
"""
from __future__ import annotations

from typing import NamedTuple


class ModuleMeta(NamedTuple):
    key: str
    label: str
    date_field: str | None


MODULES: list[ModuleMeta] = [
    ModuleMeta("sample", "样品登记", "送检日期"),
    ModuleMeta("contract", "委托合同", "签订日期"),
    ModuleMeta("task", "检测任务", None),
    ModuleMeta("method", "检测方法", None),
    ModuleMeta("instrument", "仪器设备", "检定日期"),
    ModuleMeta("standard", "标准物质", "开封日期"),
    ModuleMeta("result", "检测结果", None),
    ModuleMeta("report", "检测报告", "报告日期"),
    ModuleMeta("boundary", "分包检测", "送样日期"),
    ModuleMeta("abnormal", "不符合项", None),
    ModuleMeta("envmonitor", "环境监控", "监测时间"),
    ModuleMeta("blind", "盲样考核", "考核日期"),
    ModuleMeta("ability", "能力验证", "上报日期"),
    ModuleMeta("intermediate", "中间液配制", "配制日期"),
    ModuleMeta("audit", "内审检查", "内审日期"),
    ModuleMeta("certification", "认证认可", "获证日期"),
    ModuleMeta("quality", "质控样", "进库日期"),
    ModuleMeta("reagent2", "试剂管理", None),
    ModuleMeta("waste", "实验废液", "产生日期"),
    ModuleMeta("opinion", "客户反馈", "反馈日期"),
]

MODULE_KEYS: tuple[str, ...] = tuple(item.key for item in MODULES)
MODULE_LABELS: dict[str, str] = {item.key: item.label for item in MODULES}
MODULE_DATE_FIELDS: dict[str, str | None] = {item.key: item.date_field for item in MODULES}
