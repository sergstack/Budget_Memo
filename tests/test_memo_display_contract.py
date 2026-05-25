from __future__ import annotations

from pathlib import Path

from src.memo_display_contract import (
    MemoActionItem,
    MemoBlock,
    MemoChart,
    MemoDisplayContract,
    MemoSection,
    MemoTable,
    contract_from_dict,
    contract_to_dict,
    validate_display_contract,
)


def minimal_contract(block: MemoBlock | None = None, depth_mode: str = "short") -> MemoDisplayContract:
    return MemoDisplayContract(
        memo_id="memo_01",
        memo_profile="executive_yoy_mom_budget_memo",
        depth_mode=depth_mode,
        period="2026-04",
        audience="CFO",
        title="Budget memo",
        status_line="Draft display contract",
        sections=[
            MemoSection(
                section_id="summary",
                title="Executive summary",
                blocks=[block or MemoBlock(block_type="paragraph", text="Summary text.")],
            )
        ],
        evidence_references=["qa/evidence.md"],
    )


def test_valid_minimal_short_memo_contract_passes() -> None:
    assert validate_display_contract(minimal_contract()) == []


def test_valid_table_block_with_matching_row_widths_passes() -> None:
    contract = minimal_contract(
        MemoBlock(
            block_type="table",
            table=MemoTable(headers=["Metric", "Value"], rows=[["Revenue", "100"], ["Cost", "80"]]),
        )
    )

    assert validate_display_contract(contract) == []


def test_unknown_block_type_fails() -> None:
    errors = validate_display_contract(minimal_contract(MemoBlock(block_type="unknown")))

    assert any("unknown block_type" in error for error in errors)


def test_table_row_width_mismatch_fails() -> None:
    contract = minimal_contract(
        MemoBlock(
            block_type="table",
            table=MemoTable(headers=["Metric", "Value"], rows=[["Revenue", "100", "extra"]]),
        )
    )

    assert any("width mismatch" in error for error in validate_display_contract(contract))


def test_missing_chart_id_fails() -> None:
    contract = minimal_contract(MemoBlock(block_type="chart", chart=MemoChart(chart_id="", title="Budget trend")))

    assert any("chart_id and title" in error for error in validate_display_contract(contract))


def test_invalid_depth_mode_fails() -> None:
    errors = validate_display_contract(minimal_contract(depth_mode="presentation"))

    assert any("invalid depth_mode" in error for error in errors)


def test_action_table_without_status_or_candidate_final_marker_fails() -> None:
    contract = minimal_contract(
        MemoBlock(
            block_type="action_table",
            action_items=[MemoActionItem(action="Check variance", status="", marker="approved")],
        )
    )

    errors = validate_display_contract(contract)
    assert any("missing status" in error for error in errors)
    assert any("candidate or final" in error for error in errors)


def test_appendix_only_evidence_block_in_body_fails() -> None:
    contract = minimal_contract(MemoBlock(block_type="evidence_appendix", appendix_only=True))

    assert any("outside appendix" in error for error in validate_display_contract(contract))


def test_round_trip_to_from_dict_preserves_key_fields() -> None:
    contract = minimal_contract(
        MemoBlock(
            block_type="action_table",
            action_items=[MemoActionItem(action="Review owner", status="open", marker="candidate")],
        ),
        depth_mode="depth_2_management_memo",
    )

    restored = contract_from_dict(contract_to_dict(contract))

    assert restored == contract
    assert restored.memo_id == "memo_01"
    assert restored.sections[0].blocks[0].action_items[0].marker == "candidate"


def test_contract_tests_do_not_create_generated_artifacts() -> None:
    generated_paths = [
        Path("01_raw"),
        Path("02_stage"),
        Path("03_marts"),
        Path("04_charts"),
        Path("04_signals"),
        Path("05_evidence"),
        Path("05_llm_package"),
        Path("06_reports"),
        Path("07_qa"),
        Path("99_archive"),
    ]
    before = {path: path.stat().st_mtime_ns if path.exists() else None for path in generated_paths}

    validate_display_contract(minimal_contract())

    after = {path: path.stat().st_mtime_ns if path.exists() else None for path in generated_paths}
    assert after == before
