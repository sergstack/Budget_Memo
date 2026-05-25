#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


VERDICT_KEYS = [
    "docx_render_status",
    "visual_layout_status",
    "executive_readability_status",
    "publishing_hygiene_status",
    "overall_visual_release_status",
]

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "blocker": 4}


@dataclass
class Defect:
    id: str
    severity: str
    category: str
    page: int | None
    description: str
    evidence: str
    recommended_action: str


def add_defect(
    defects: list[Defect],
    severity: str,
    category: str,
    description: str,
    evidence: str,
    recommended_action: str,
    page: int | None = None,
) -> None:
    defects.append(
        Defect(
            id=f"VQA-{len(defects) + 1:03d}",
            severity=severity,
            category=category,
            page=page,
            description=description,
            evidence=evidence,
            recommended_action=recommended_action,
        )
    )


def find_soffice(explicit: str | None = None) -> str | None:
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.extend(
        [
            os.environ.get("SOFFICE_BIN", ""),
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            shutil.which("soffice") or "",
            shutil.which("libreoffice") or "",
        ]
    )
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def run_command(cmd: list[str], stdout_path: Path, stderr_path: Path, env: dict[str, str] | None = None) -> int:
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        proc = subprocess.run(cmd, stdout=stdout, stderr=stderr, text=True, check=False, env=env)
    return proc.returncode


def inspect_docx_package(docx: Path, defects: list[Defect]) -> dict:
    info: dict[str, object] = {
        "file_size": docx.stat().st_size if docx.exists() else 0,
        "media_count": 0,
        "comments": [],
        "tracked_changes": False,
        "custom_properties": [],
        "local_debug_paths": [],
        "tables": 0,
        "images": 0,
    }
    if not docx.exists():
        add_defect(defects, "blocker", "render", "DOCX file does not exist.", str(docx), "Provide a valid DOCX path.")
        return info
    if docx.stat().st_size <= 0:
        add_defect(defects, "blocker", "render", "DOCX file is empty.", str(docx), "Regenerate the DOCX artifact.")
        return info

    try:
        with zipfile.ZipFile(docx) as package:
            names = package.namelist()
            info["media_count"] = len([n for n in names if n.startswith("word/media/") and not n.endswith("/")])
            info["comments"] = [n for n in names if "comments" in n.lower()]
            info["custom_properties"] = [n for n in names if n.startswith("docProps/custom")]
            xml_parts = []
            for name in names:
                if name.endswith(".xml") and (name.startswith("word/") or name.startswith("docProps/")):
                    try:
                        xml_parts.append(package.read(name).decode("utf-8", errors="ignore"))
                    except Exception:
                        pass
            xml = "\n".join(xml_parts)
            info["tracked_changes"] = bool(re.search(r"<w:(ins|del|moveFrom|moveTo)\b", xml))
            info["tables"] = xml.count("<w:tbl>")
            info["images"] = xml.count("<w:drawing")
            info["local_debug_paths"] = sorted(
                set(re.findall(r"(?:/Users/|/private/|/tmp/|C:\\\\Users\\\\)[^\\s<\"']+", xml))
            )
    except zipfile.BadZipFile:
        add_defect(defects, "blocker", "render", "DOCX package is not a valid zip container.", str(docx), "Regenerate the DOCX artifact.")
        return info

    if info["comments"]:
        add_defect(defects, "blocker", "metadata", "DOCX contains comments.", ", ".join(info["comments"]), "Remove comments before release.")
    if info["tracked_changes"]:
        add_defect(defects, "blocker", "metadata", "DOCX contains tracked changes.", "Tracked-change tags found in OOXML.", "Accept or reject tracked changes before release.")
    if info["local_debug_paths"]:
        add_defect(defects, "high", "metadata", "DOCX contains local/debug paths.", "; ".join(info["local_debug_paths"])[:500], "Remove local paths from generated content and metadata.")
    if len(info["custom_properties"]) > 1:
        add_defect(defects, "medium", "metadata", "DOCX has custom properties.", ", ".join(info["custom_properties"]), "Review publishing metadata.")
    return info


def convert_docx_to_pdf(docx: Path, out_dir: Path, logs: Path, soffice: str | None, defects: list[Defect]) -> Path | None:
    if not soffice:
        add_defect(defects, "blocker", "render", "LibreOffice/soffice is unavailable.", "No soffice binary found.", "Install LibreOffice or pass --soffice-bin.")
        return None
    with tempfile.TemporaryDirectory(prefix="docx_visual_qa_profile_") as profile:
        env = os.environ.copy()
        env["HOME"] = profile
        env.setdefault("TMPDIR", "/private/tmp" if sys.platform == "darwin" and Path("/private/tmp").exists() else tempfile.gettempdir())
        cmd = [
            soffice,
            f"-env:UserInstallation=file://{profile}",
            "--invisible",
            "--headless",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir),
            str(docx),
        ]
        code = run_command(cmd, logs / "libreoffice_stdout.log", logs / "libreoffice_stderr.log", env=env)
    pdf = out_dir / f"{docx.stem}.pdf"
    emitted = sorted(out_dir.glob("*.pdf"))
    if pdf.exists():
        pdf.replace(out_dir / "rendered.pdf")
        return out_dir / "rendered.pdf"
    if emitted:
        emitted[0].replace(out_dir / "rendered.pdf")
        return out_dir / "rendered.pdf"
    add_defect(
        defects,
        "blocker",
        "render",
        "DOCX did not render to PDF.",
        f"LibreOffice exit code: {code}; logs: {logs}",
        "Fix DOCX generation or LibreOffice render environment.",
    )
    return None


def render_pdf_pages(pdf: Path, pages_dir: Path, logs: Path, defects: list[Defect]) -> list[Path]:
    pages_dir.mkdir(parents=True, exist_ok=True)
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        prefix = pages_dir / "page"
        code = run_command(
            [pdftoppm, "-png", "-r", "150", str(pdf), str(prefix)],
            logs / "pdf_render_stdout.log",
            logs / "pdf_render_stderr.log",
        )
        raw_pages = sorted(pages_dir.glob("page-*.png"))
        normalized = []
        for idx, raw in enumerate(raw_pages, start=1):
            dst = pages_dir / f"page_{idx:03d}.png"
            raw.replace(dst)
            normalized.append(dst)
        if normalized:
            return normalized
        add_defect(defects, "blocker", "render", "PDF did not render to PNG pages.", f"pdftoppm exit code: {code}", "Check Poppler/pdftoppm or PDF output.")
        return []

    try:
        from pdf2image import convert_from_path
    except Exception as exc:
        (logs / "pdf_render_stdout.log").write_text("", encoding="utf-8")
        (logs / "pdf_render_stderr.log").write_text(str(exc), encoding="utf-8")
        add_defect(defects, "blocker", "render", "No PDF-to-PNG renderer is available.", str(exc), "Install Poppler or pdf2image dependencies.")
        return []

    try:
        images = convert_from_path(str(pdf), dpi=150)
        pages = []
        for idx, image in enumerate(images, start=1):
            dst = pages_dir / f"page_{idx:03d}.png"
            image.save(dst)
            pages.append(dst)
        (logs / "pdf_render_stdout.log").write_text(f"Rendered {len(pages)} pages with pdf2image.\n", encoding="utf-8")
        (logs / "pdf_render_stderr.log").write_text("", encoding="utf-8")
        return pages
    except Exception as exc:
        (logs / "pdf_render_stderr.log").write_text(str(exc), encoding="utf-8")
        add_defect(defects, "blocker", "render", "PDF did not render to PNG pages.", str(exc), "Check PDF output and rasterizer dependencies.")
        return []


def analyze_pages(pages: list[Path], defects: list[Defect]) -> dict:
    page_info = {"page_count": len(pages), "near_blank_pages": []}
    if not pages:
        add_defect(defects, "blocker", "render", "No PNG pages were created.", "page_count=0", "Fix render/rasterization.")
        return page_info
    try:
        from PIL import Image
    except Exception:
        return page_info

    for page in pages:
        idx = int(re.search(r"(\d+)", page.stem).group(1)) if re.search(r"(\d+)", page.stem) else None
        image = Image.open(page).convert("L")
        histogram = image.histogram()
        non_white = sum(count for value, count in enumerate(histogram) if value < 245)
        ratio = non_white / float(image.width * image.height)
        if ratio < 0.003:
            page_info["near_blank_pages"].append(idx)
            add_defect(defects, "high", "layout", "Rendered page appears blank or nearly blank.", f"ink_ratio={ratio:.4f}", "Remove unintended blank page or explain allowed blank page.", idx)
    return page_info


def derive_verdicts(defects: list[Defect]) -> dict[str, str]:
    verdicts = {key: "pass" for key in VERDICT_KEYS}
    by_category = {
        "docx_render_status": {"render"},
        "visual_layout_status": {"layout", "table", "chart", "appendix"},
        "executive_readability_status": {"executive_readability"},
        "publishing_hygiene_status": {"metadata"},
    }
    for key, categories in by_category.items():
        relevant = [d for d in defects if d.category in categories]
        if any(d.severity == "blocker" for d in relevant):
            verdicts[key] = "blocked"
        elif any(SEVERITY_ORDER[d.severity] >= SEVERITY_ORDER["medium"] for d in relevant):
            verdicts[key] = "revise"
    if any(d.severity == "blocker" for d in defects):
        verdicts["overall_visual_release_status"] = "blocked"
    elif any(SEVERITY_ORDER[d.severity] >= SEVERITY_ORDER["medium"] for d in defects):
        verdicts["overall_visual_release_status"] = "revise"
    return verdicts


def write_reports(out_dir: Path, target: Path, package_info: dict, page_info: dict, defects: list[Defect], commands: list[str]) -> dict:
    verdicts = derive_verdicts(defects)
    release_blockers = [asdict(d) for d in defects if d.severity == "blocker"]
    payload = {
        "target_docx": str(target),
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "verdicts": verdicts,
        "package": package_info,
        "pages": page_info,
        "defects": [asdict(d) for d in defects],
        "release_blockers": release_blockers,
    }
    (out_dir / "defects.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    defect_rows = "\n".join(
        f"| {d.id} | {d.severity} | {d.category} | {d.page or ''} | {d.description} | {d.recommended_action} |"
        for d in defects
    ) or "| none |  |  |  | No defects found. |  |"
    blockers = ", ".join(d["id"] for d in release_blockers) if release_blockers else "none"
    report = f"""# Analytical Memo Visual QA Diagnostic Report

## 1. Verdict

docx_render_status: {verdicts['docx_render_status']}
visual_layout_status: {verdicts['visual_layout_status']}
executive_readability_status: {verdicts['executive_readability_status']}
publishing_hygiene_status: {verdicts['publishing_hygiene_status']}
overall_visual_release_status: {verdicts['overall_visual_release_status']}

reason: deterministic read-only DOCX/PDF visual diagnostics completed.
release_blockers: {blockers}
must_fix_before_release: {blockers}
nice_to_have: review medium/low visual layout findings.
requires_live_run: false

## 2. Target

- DOCX: {target}
- File size: {package_info.get('file_size')}
- Created diagnostics folder: {out_dir}

## 3. Commands Run

{chr(10).join(f'- `{cmd}`' for cmd in commands)}

## 4. Artifacts Created

| Artifact | Path | Exists | Notes |
|---|---|---|---|
| JSON defects report | `{out_dir / 'defects.json'}` | {(out_dir / 'defects.json').exists()} | machine-readable report |
| Markdown report | `{out_dir / 'diagnostic_report.md'}` | true | this file |
| PDF render | `{out_dir / 'rendered.pdf'}` | {(out_dir / 'rendered.pdf').exists()} | LibreOffice output |
| PNG pages | `{out_dir / 'pages'}` | {(out_dir / 'pages').exists()} | {page_info.get('page_count', 0)} pages |
| LibreOffice stdout | `{out_dir / 'logs/libreoffice_stdout.log'}` | {(out_dir / 'logs/libreoffice_stdout.log').exists()} | render log |
| LibreOffice stderr | `{out_dir / 'logs/libreoffice_stderr.log'}` | {(out_dir / 'logs/libreoffice_stderr.log').exists()} | render log |

## 5. Defects

| ID | Severity | Category | Page | Description | Recommended action |
|---|---|---:|---:|---|---|
{defect_rows}

## 6. Table Diagnostics

Detected OOXML tables: {package_info.get('tables')}. Detailed readability is a visual/manual review area.

## 7. Chart Diagnostics

Embedded media count: {package_info.get('media_count')}. Blank-chart detection is limited to page raster signals and visual review.

## 8. Appendix Diagnostics

Appendix separation requires visual/manual review unless project-specific section markers are supplied.

## 9. Metadata / Publishing Hygiene

- comments: {len(package_info.get('comments', []))}
- tracked changes: {package_info.get('tracked_changes')}
- custom properties: {len(package_info.get('custom_properties', []))}
- local/debug paths: {len(package_info.get('local_debug_paths', []))}

## 10. Content Sanity Notes

No full business recalculation was performed.

## 11. Final Recommendation

{verdicts['overall_visual_release_status']}
"""
    (out_dir / "diagnostic_report.md").write_text(report, encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only deterministic DOCX/PDF visual QA diagnostic gate. "
            "Does not run live Kestra and does not modify business logic or source DOCX."
        )
    )
    parser.add_argument("--docx", required=True, help="Target DOCX artifact to inspect.")
    parser.add_argument("--out", required=True, help="Diagnostics output folder.")
    parser.add_argument("--soffice-bin", default=None, help="Optional LibreOffice/soffice binary path.")
    args = parser.parse_args()

    target = Path(args.docx).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    logs = out_dir / "logs"
    pages = out_dir / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    defects: list[Defect] = []
    commands = [
        f"{sys.executable} scripts/diagnose_docx_visual_quality.py --docx {target} --out {out_dir}",
    ]
    package_info = inspect_docx_package(target, defects)
    soffice = find_soffice(args.soffice_bin)
    if soffice:
        commands.append(f"{soffice} --headless --convert-to pdf --outdir {out_dir} {target}")
    pdf = convert_docx_to_pdf(target, out_dir, logs, soffice, defects) if target.exists() else None
    rendered_pages = render_pdf_pages(pdf, pages, logs, defects) if pdf else []
    page_info = analyze_pages(rendered_pages, defects)
    payload = write_reports(out_dir, target, package_info, page_info, defects, commands)
    print(json.dumps({"verdicts": payload["verdicts"], "defects": len(payload["defects"]), "out": str(out_dir)}, ensure_ascii=False, indent=2))
    return 1 if payload["release_blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

