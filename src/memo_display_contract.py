from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_BLOCK_TYPES = {
    "paragraph",
    "bullet_list",
    "kpi_cards",
    "table",
    "chart",
    "limitation_box",
    "action_table",
    "evidence_appendix",
}

ALLOWED_DEPTH_MODES = {
    "short",
    "standard",
    "deep",
    "action",
    "depth_1_executive_brief",
    "depth_2_management_memo",
    "depth_3_finance_working_package",
    "depth_4_operating_model",
}

ALLOWED_ACTION_MARKERS = {"candidate", "final"}


@dataclass(frozen=True)
class MemoTable:
    headers: list[str]
    rows: list[list[str]] = field(default_factory=list)
    caption: str = ""


@dataclass(frozen=True)
class MemoChart:
    chart_id: str
    title: str
    caption: str = ""
    source_ref: str = ""


@dataclass(frozen=True)
class MemoKpiCard:
    label: str
    value: str
    status: str = ""
    source_ref: str = ""


@dataclass(frozen=True)
class MemoLimitation:
    title: str
    text: str
    severity: str = ""


@dataclass(frozen=True)
class MemoActionItem:
    action: str
    owner: str = ""
    status: str = ""
    marker: str = "candidate"
    due_date: str = ""
    evidence_ref: str = ""


@dataclass(frozen=True)
class MemoBlock:
    block_type: str
    text: str = ""
    bullets: list[str] = field(default_factory=list)
    kpi_cards: list[MemoKpiCard] = field(default_factory=list)
    table: MemoTable | None = None
    chart: MemoChart | None = None
    limitation: MemoLimitation | None = None
    action_items: list[MemoActionItem] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    appendix_only: bool = False


@dataclass(frozen=True)
class MemoSection:
    section_id: str
    title: str
    blocks: list[MemoBlock] = field(default_factory=list)
    is_appendix: bool = False


@dataclass(frozen=True)
class MemoDisplayContract:
    memo_id: str
    memo_profile: str
    depth_mode: str
    period: str
    audience: str
    title: str
    status_line: str
    sections: list[MemoSection] = field(default_factory=list)
    evidence_references: list[str] = field(default_factory=list)
    appendix: list[MemoBlock] = field(default_factory=list)
    subtitle: str = ""


def validate_display_contract(contract: MemoDisplayContract) -> list[str]:
    errors: list[str] = []
    if not contract.title.strip():
        errors.append("missing title")
    if contract.depth_mode not in ALLOWED_DEPTH_MODES:
        errors.append(f"invalid depth_mode: {contract.depth_mode}")
    if not contract.sections:
        errors.append("missing sections")

    for section_index, section in enumerate(contract.sections):
        if not section.blocks:
            errors.append(f"section[{section_index}] has no blocks")
        for block_index, block in enumerate(section.blocks):
            location = f"section[{section_index}].block[{block_index}]"
            _validate_block(block, errors, location, section.is_appendix)

    for block_index, block in enumerate(contract.appendix):
        _validate_block(block, errors, f"appendix.block[{block_index}]", True)

    return errors


def contract_to_dict(contract: MemoDisplayContract) -> dict[str, Any]:
    return asdict(contract)


def contract_from_dict(data: dict[str, Any]) -> MemoDisplayContract:
    sections = [_section_from_dict(section) for section in data.get("sections", [])]
    appendix = [_block_from_dict(block) for block in data.get("appendix", [])]
    return MemoDisplayContract(
        memo_id=data.get("memo_id", ""),
        memo_profile=data.get("memo_profile", ""),
        depth_mode=data.get("depth_mode", ""),
        period=data.get("period", ""),
        audience=data.get("audience", ""),
        title=data.get("title", ""),
        subtitle=data.get("subtitle", ""),
        status_line=data.get("status_line", ""),
        sections=sections,
        evidence_references=list(data.get("evidence_references", [])),
        appendix=appendix,
    )


def _validate_block(block: MemoBlock, errors: list[str], location: str, is_appendix: bool) -> None:
    if block.block_type not in ALLOWED_BLOCK_TYPES:
        errors.append(f"{location} unknown block_type: {block.block_type}")
        return
    if block.block_type == "table":
        _validate_table(block.table, errors, location)
    if block.block_type == "chart" and (
        block.chart is None or not block.chart.chart_id.strip() or not block.chart.title.strip()
    ):
        errors.append(f"{location} chart block requires chart_id and title")
    if block.block_type == "action_table":
        _validate_action_table(block.action_items, errors, location)
    if block.block_type == "evidence_appendix" and block.appendix_only and not is_appendix:
        errors.append(f"{location} appendix-only evidence block appears outside appendix")


def _validate_table(table: MemoTable | None, errors: list[str], location: str) -> None:
    if table is None:
        errors.append(f"{location} table block requires table")
        return
    if not table.headers:
        errors.append(f"{location} table requires header")
        return
    width = len(table.headers)
    for row_index, row in enumerate(table.rows):
        if len(row) != width:
            errors.append(f"{location} table row[{row_index}] width mismatch")


def _validate_action_table(action_items: list[MemoActionItem], errors: list[str], location: str) -> None:
    if not action_items:
        errors.append(f"{location} action table requires action_items")
        return
    for item_index, item in enumerate(action_items):
        if not item.status.strip():
            errors.append(f"{location} action_items[{item_index}] missing status")
        if item.marker not in ALLOWED_ACTION_MARKERS:
            errors.append(f"{location} action_items[{item_index}] marker must be candidate or final")


def _section_from_dict(data: dict[str, Any]) -> MemoSection:
    return MemoSection(
        section_id=data.get("section_id", ""),
        title=data.get("title", ""),
        blocks=[_block_from_dict(block) for block in data.get("blocks", [])],
        is_appendix=bool(data.get("is_appendix", False)),
    )


def _block_from_dict(data: dict[str, Any]) -> MemoBlock:
    return MemoBlock(
        block_type=data.get("block_type", ""),
        text=data.get("text", ""),
        bullets=list(data.get("bullets", [])),
        kpi_cards=[MemoKpiCard(**card) for card in data.get("kpi_cards", [])],
        table=MemoTable(**data["table"]) if data.get("table") else None,
        chart=MemoChart(**data["chart"]) if data.get("chart") else None,
        limitation=MemoLimitation(**data["limitation"]) if data.get("limitation") else None,
        action_items=[MemoActionItem(**item) for item in data.get("action_items", [])],
        evidence_refs=list(data.get("evidence_refs", [])),
        appendix_only=bool(data.get("appendix_only", False)),
    )
