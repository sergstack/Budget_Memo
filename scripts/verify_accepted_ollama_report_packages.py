from __future__ import annotations

import argparse
import json
import math
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MEMO02_QA = (
    PROJECT_ROOT
    / "06_reports/02_monthly_plan_fact_memo/07_qa/factory_ollama_consensus_20260522_185632"
)
DEPTHS = ["short", "standard", "deep", "action"]


def as_path(value: Any) -> Path | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan" or text.lower() == "n/a":
        return None
    return PROJECT_ROOT / text


def rel(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def docx_media_count(path: Path | None) -> int | None:
    if path is None or not path.exists():
        return None
    with zipfile.ZipFile(path) as zf:
        return sum(1 for name in zf.namelist() if name.startswith("word/media/"))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def status_from_json(path: Path, keys: list[str]) -> str:
    if not path.exists():
        return "missing"
    data = load_json(path)
    for key in keys:
        value = data.get(key)
        if value is not None:
            return str(value)
    return "missing_key"


def chart_manifest_check(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"exists": False, "rows": 0, "limitations_nonempty": False, "chart_files_exist": False}
    if not path.exists():
        return {"exists": False, "rows": 0, "limitations_nonempty": False, "chart_files_exist": False}
    df = pd.read_excel(path)
    limit_cols = [col for col in ["limitations", "limitation"] if col in df.columns]
    limitations_nonempty = bool(limit_cols) and all(
        df[col].fillna("").astype(str).str.strip().ne("").all() for col in limit_cols
    )
    path_cols = [col for col in ["output_path", "output_paths"] if col in df.columns]
    chart_paths: list[Path] = []
    for col in path_cols:
        for raw in df[col].dropna().astype(str):
            for item in raw.split(";"):
                item = item.strip()
                if item:
                    chart_paths.append(PROJECT_ROOT / item)
    chart_files_exist = bool(chart_paths) and all(path.exists() for path in chart_paths)
    return {
        "exists": True,
        "rows": int(len(df)),
        "limitations_nonempty": limitations_nonempty,
        "chart_files_exist": chart_files_exist,
    }


def memo02_qa_status(qa_dir: Path, depth: str) -> dict[str, Any]:
    prefix = f"02_monthly_plan_fact_memo__{depth}"
    render_summary = qa_dir / "libreoffice_render_summary.json"
    render = "missing"
    if render_summary.exists():
        render_data = load_json(render_summary)
        render = str(render_data.get(depth, {}).get("status", "missing"))
    return {
        "text_qa": status_from_json(qa_dir / f"{prefix}__text_qa.json", ["qa_status"]),
        "preflight": status_from_json(qa_dir / f"{prefix}__judge_preflight.json", ["preflight_status"]),
        "final_judge": status_from_json(qa_dir / f"{prefix}__final_judge.json", ["verdict"]),
        "render": render,
        "source_of_truth": rel(qa_dir),
    }


def read_registry(path: Path) -> dict[str, pd.DataFrame]:
    return pd.read_excel(path, sheet_name=None)


def build_records(registry: dict[str, pd.DataFrame], memo02_qa_dir: Path) -> list[dict[str, Any]]:
    depth_outputs = registry["02_DEPTH_OUTPUTS"]
    qa_status = registry["03_QA_STATUS"]
    chart_manifests = registry["05_CHART_MANIFESTS"]
    qa_by_key = {
        (str(row.memo_id), str(row.depth)): row
        for row in qa_status.itertuples(index=False)
    }
    chart_by_memo = {
        str(row.memo_id): row
        for row in chart_manifests.itertuples(index=False)
    }
    records: list[dict[str, Any]] = []
    for row in depth_outputs.itertuples(index=False):
        memo_id = str(row.memo_id)
        depth = str(row.depth)
        final_docx = as_path(row.final_docx)
        final_md = as_path(row.final_md)
        final_xlsx = as_path(row.final_xlsx)
        expected_media = int(row.media_required)
        actual_media = docx_media_count(final_docx)
        chart_row = chart_by_memo.get(memo_id)
        manifest_path = as_path(getattr(chart_row, "manifest_xlsx", None)) if chart_row else None
        chart_check = chart_manifest_check(manifest_path)

        if memo_id == "02_monthly_plan_fact_memo":
            qa = memo02_qa_status(memo02_qa_dir, depth)
        else:
            registry_qa = qa_by_key.get((memo_id, depth))
            qa = {
                "text_qa": str(getattr(registry_qa, "text_qa", "missing")),
                "preflight": str(getattr(registry_qa, "judge_preflight", "missing")),
                "final_judge": str(getattr(registry_qa, "final_judge", "missing")),
                "render": str(getattr(registry_qa, "render_status", "missing")),
                "source_of_truth": "06_reports/release_registry.xlsx",
            }

        checks = {
            "final_docx_exists": bool(final_docx and final_docx.exists()),
            "final_md_exists": bool(final_md and final_md.exists()),
            "final_xlsx_exists": final_xlsx is None or final_xlsx.exists(),
            "media_count_pass": actual_media is not None and actual_media >= expected_media,
            "chart_manifest_exists": bool(chart_check["exists"]),
            "chart_limitations_pass": bool(chart_check["limitations_nonempty"]),
            "chart_files_exist": bool(chart_check["chart_files_exist"]),
            "text_qa_pass": qa["text_qa"] == "pass",
            "preflight_pass": qa["preflight"] == "pass",
            "final_judge_accept": qa["final_judge"] == "accept",
            "render_pass": qa["render"] == "pass",
        }
        status = "pass" if all(checks.values()) else "fail"
        records.append(
            {
                "memo_id": memo_id,
                "depth": depth,
                "final_docx": rel(final_docx),
                "final_md": rel(final_md),
                "final_xlsx": rel(final_xlsx),
                "media_count": actual_media,
                "required_media": expected_media,
                "text_qa": qa["text_qa"],
                "preflight": qa["preflight"],
                "final_judge": qa["final_judge"],
                "render": qa["render"],
                "chart_manifest": rel(manifest_path),
                "chart_manifest_rows": chart_check["rows"],
                "chart_limitations_nonempty": chart_check["limitations_nonempty"],
                "chart_files_exist": chart_check["chart_files_exist"],
                "source_of_truth": qa["source_of_truth"],
                "checks": checks,
                "status": status,
            }
        )
    return records


def write_tsv(path: Path, records: list[dict[str, Any]]) -> None:
    headers = [
        "memo_id",
        "depth",
        "final_docx",
        "media_count",
        "required_media",
        "text_qa",
        "preflight",
        "final_judge",
        "render",
        "source_of_truth",
        "status",
    ]
    lines = ["\t".join(headers)]
    for row in records:
        lines.append("\t".join(str(row.get(col, "")) for col in headers))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(path: Path, records: list[dict[str, Any]]) -> None:
    lines = [
        "# Accepted package verification matrix",
        "",
        "| memo_id | depth | final_docx | media_count | text_qa | preflight | final_judge | render | source_of_truth | status |",
        "|---|---|---|---:|---|---|---|---|---|---|",
    ]
    for row in records:
        lines.append(
            "| {memo_id} | {depth} | `{final_docx}` | {media_count} | {text_qa} | {preflight} | {final_judge} | {render} | `{source_of_truth}` | {status} |".format(
                **row
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify accepted memo report packages without regeneration.")
    parser.add_argument("--registry", type=Path, default=PROJECT_ROOT / "06_reports/release_registry.xlsx")
    parser.add_argument("--accepted-summary", type=Path, default=PROJECT_ROOT / "06_reports/accepted_packages_summary.md")
    parser.add_argument("--memo02-qa-dir", type=Path, default=DEFAULT_MEMO02_QA)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    log_lines = [
        f"created_at={datetime.now(timezone.utc).isoformat()}",
        f"registry={rel(args.registry)} exists={args.registry.exists()}",
        f"accepted_summary={rel(args.accepted_summary)} exists={args.accepted_summary.exists()}",
        f"memo02_qa_dir={rel(args.memo02_qa_dir)} exists={args.memo02_qa_dir.exists()}",
        "mode=accepted_artifact_verification_no_ollama_no_generation",
    ]
    registry = read_registry(args.registry)
    records = build_records(registry, args.memo02_qa_dir)
    overall = "pass" if all(row["status"] == "pass" for row in records) else "fail"
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "accepted_artifact_verification_no_ollama_no_generation",
        "registry": rel(args.registry),
        "accepted_summary": rel(args.accepted_summary),
        "memo02_accepted_qa_folder": rel(args.memo02_qa_dir),
        "overall_status": overall,
        "records": records,
    }
    (out_dir / "run_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_tsv(out_dir / "run_summary.tsv", records)
    write_markdown(out_dir / "accepted_package_matrix.md", records)
    log_lines.append(f"records={len(records)}")
    log_lines.append(f"overall_status={overall}")
    (out_dir / "run.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    for idx, row in enumerate(records, start=1):
        print(f"[{idx}/{len(records)}] {row['memo_id']} / {row['depth']}: {row['status']}")
    print(f"overall_status: {overall}")
    print(f"output_dir: {rel(out_dir)}")
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
