from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "01_raw"
STAGE_SOURCE = PROJECT_ROOT / "02_stage" / "01_full_stage.csv"
MARTS_DIR = PROJECT_ROOT / "03_marts"
CHARTS_DIR = PROJECT_ROOT / "04_charts"
REPORTS_DIR = PROJECT_ROOT / "06_reports"
MEMO_01_DIR = REPORTS_DIR / "01_executive_yoy_mom_budget_memo"
MEMO_01_DRAFT_DIR = MEMO_01_DIR / "draft"
MEMO_01_SOURCE_REFS_DIR = MEMO_01_DIR / "source_refs"
LLM_DIR = PROJECT_ROOT / "05_llm_package"
QA_DIR = PROJECT_ROOT / "07_qa"

MART_ARTIFACTS = {
    "mart_main_full_budget": MARTS_DIR / "mart_main_full_budget.parquet",
    "mart_flow_base_month": MARTS_DIR / "mart_flow_base_month.parquet",
    "mart_signal_catalog_full": MARTS_DIR / "mart_signal_catalog_full.parquet",
    "mart_main_compact_executive_yoy_mom": MARTS_DIR / "mart_main_compact_executive_yoy_mom.parquet",
}

PROFILE_ARTIFACTS = {
    "memo_profile_catalog": MARTS_DIR / "memo_profile_catalog.parquet",
    "memo_depth_mode_catalog": MARTS_DIR / "memo_depth_mode_catalog.parquet",
    "profile_readiness_matrix": MARTS_DIR / "profile_readiness_matrix.parquet",
    "profile_preview_index": MARTS_DIR / "profile_preview_index.parquet",
}

EXCEL_ARTIFACTS = {
    MARTS_DIR / "mart_full_package.xlsx": [
        "01_Полный_MART",
        "02_IN_OUT_База",
        "03_Каталог_Сигналов",
        "04_Compact_для_Руководства",
        "11_Юрлица",
        "12_Валюты",
        "13_Юрлица_Валюты",
        "15_Timing_Кандидаты",
        "16_Refunds",
        "17_Пороги",
        "22_Полный_MART_Строки",
    ],
    MARTS_DIR / "memo_profile_catalog.xlsx": ["Профили_Записок"],
    MARTS_DIR / "memo_depth_mode_catalog.xlsx": ["Режимы_Глубины"],
    MARTS_DIR / "profile_readiness_matrix.xlsx": ["Матрица_Готовности"],
    MARTS_DIR / "profile_preview_index.xlsx": ["Preview_Профилей"],
}

PROFILE_GOVERNANCE_FIELDS = {
    "block_status",
    "output_layer",
    "publish_rule",
    "stop_conditions",
    "acceptance_criteria",
    "evidence_requirement",
    "confidence_rule",
    "action_requirement",
}

PROFILE_SIGNAL_FIELDS = {
    "eligible_memo_profiles",
    "primary_memo_profile",
    "memo_section",
    "profile_priority",
    "release_priority",
    "profile_readiness_status",
}

CHART_REQUIRED_IDS = {
    "CH_EXEC_001_PLAN_FACT_TOP_ABS",
    "CH_EXEC_002_YOY_TOP_SHIFT",
    "CH_EXEC_003_MOM_INSTABILITY",
    "CH_EXEC_004_LOCALIZATION_ARTICLE_CFO",
    "CH_EXEC_005_PLANNING_RISK",
    "CH_EXEC_006_IN_CONTEXT",
    "CH_EXEC_007_FLOW_BASE",
    "CH_EXEC_008_QA_LIMITATIONS",
}

MANAGEMENT_SHEET_GRAINS = {
    "01_Полный_MART": ["Месяц", "Год", "Тип периода", "Тип статьи", "Статья 1", "Статья 2", "Статья", "ЦФО", "Контрагент"],
    "05_Plan_Fact": ["Месяц", "Статья", "ЦФО"],
    "06_YoY": ["Статья", "ЦФО", "Год", "Номер месяца"],
    "07_MoM": ["Статья", "ЦФО"],
    "08_Локализация": ["Статья", "ЦФО"],
    "09_Плановый_Риск": ["Статья", "ЦФО"],
    "10_Контрагенты": ["Контрагент"],
    "11_Юрлица": ["Юр. лицо"],
    "12_Валюты": ["Валюта"],
    "13_Юрлица_Валюты": ["Юр. лицо", "Валюта"],
    "15_Timing_Кандидаты": ["Месяц", "Статья", "ЦФО", "Контрагент"],
    "16_Refunds": ["Месяц", "Статья", "ЦФО", "Контрагент"],
}

PIVOT_SAFE_MAIN_GRAIN = [
    "period_month",
    "period_year",
    "period_type",
    "article_type",
    "article_level_1",
    "article_level_2",
    "article",
    "cfo",
    "counterparty",
]


class AcceptedMartAndProfileContractTest(unittest.TestCase):
    """Contract tests for the accepted MART/profile architecture.

    The previous version of this file asserted the retired downstream report
    contract: LLM package, charts, and final_memo.docx. Those outputs are now
    legacy artifacts and are intentionally not required by the accepted MART
    rebuild/profile-preview tasks.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.mart_qa = json.loads((QA_DIR / "mart_rebuild_qa_report.json").read_text(encoding="utf-8"))
        cls.profile_qa = json.loads((QA_DIR / "memo_profile_catalog_qa_report.json").read_text(encoding="utf-8"))
        cls.depth_modes_qa = json.loads((QA_DIR / "depth_modes_qa.json").read_text(encoding="utf-8"))
        chart_qa_path = QA_DIR / "chart_qa" / "chart_qa_report.json"
        cls.chart_qa = json.loads(chart_qa_path.read_text(encoding="utf-8")) if chart_qa_path.exists() else None
        report_contract_qa_path = QA_DIR / "report_contract_qa.json"
        cls.report_contract_qa = (
            json.loads(report_contract_qa_path.read_text(encoding="utf-8"))
            if report_contract_qa_path.exists()
            else None
        )
        draft_package_qa_path = QA_DIR / "draft_data_package_qa.json"
        cls.draft_package_qa = (
            json.loads(draft_package_qa_path.read_text(encoding="utf-8"))
            if draft_package_qa_path.exists()
            else None
        )
        controlled_draft_qa_path = QA_DIR / "controlled_draft_memo_qa.json"
        cls.controlled_draft_qa = (
            json.loads(controlled_draft_qa_path.read_text(encoding="utf-8"))
            if controlled_draft_qa_path.exists()
            else None
        )
        memo_draft_qa_path = QA_DIR / "executive_yoy_mom_memo_draft_grounding_qa.json"
        cls.memo_draft_qa = (
            json.loads(memo_draft_qa_path.read_text(encoding="utf-8"))
            if memo_draft_qa_path.exists()
            else None
        )

    def test_required_mart_artifacts_exist(self) -> None:
        self.assertTrue(STAGE_SOURCE.exists())
        for name, path in MART_ARTIFACTS.items():
            self.assertTrue(path.exists(), name)
            self.assertGreater(path.stat().st_size, 0, name)

    def test_profile_artifacts_exist(self) -> None:
        for name, path in PROFILE_ARTIFACTS.items():
            self.assertTrue(path.exists(), name)
            self.assertGreater(path.stat().st_size, 0, name)

    def test_memo_profile_catalog_has_18_profiles_and_r1_active(self) -> None:
        catalog = pd.read_parquet(PROFILE_ARTIFACTS["memo_profile_catalog"])
        self.assertEqual(len(catalog), 18)
        self.assertEqual(catalog["profile_code"].nunique(), 18)
        r1_profiles = catalog[catalog["release_priority"].eq("R1")]
        self.assertFalse(r1_profiles.empty)
        self.assertTrue(r1_profiles["profile_status"].eq("active").all())

    def test_memo_profile_catalog_has_governance_fields(self) -> None:
        catalog = pd.read_parquet(PROFILE_ARTIFACTS["memo_profile_catalog"])
        self.assertTrue(PROFILE_GOVERNANCE_FIELDS.issubset(catalog.columns))
        self.assertTrue(set(catalog["block_status"]).issubset({"must", "should", "conditional", "optional"}))
        self.assertTrue(
            set(catalog["output_layer"]).issubset(
                {"executive_memo", "finance_working_package", "system_layer", "operating_model"}
            )
        )
        forecast = catalog.loc[catalog["profile_code"].eq("forecast_run_rate_memo")]
        self.assertEqual(forecast["block_status"].iloc[0], "optional")
        flow_profiles = catalog[catalog["source_signal_types"].str.contains("flow_pressure", regex=False)]
        self.assertTrue(flow_profiles["evidence_requirement"].str.contains("Definition Card", regex=False).all())
        self.assertTrue({"default_depth_mode", "allowed_depth_modes"}.issubset(catalog.columns))
        self.assertTrue(catalog["default_depth_mode"].fillna("").ne("").all())

    def test_depth_mode_catalog_contract(self) -> None:
        depth_modes = pd.read_parquet(PROFILE_ARTIFACTS["memo_depth_mode_catalog"])
        self.assertEqual(len(depth_modes), 4)
        self.assertEqual(
            set(depth_modes["depth_mode"]),
            {
                "depth_1_executive_brief",
                "depth_2_management_memo",
                "depth_3_finance_working_package",
                "depth_4_operating_model",
            },
        )
        required = {
            "depth_mode_ru_name",
            "depth_mode_status",
            "audience",
            "included_sections",
            "excluded_sections",
            "chart_policy",
            "evidence_policy",
            "appendix_policy",
            "action_policy",
            "output_artifact_policy",
            "stop_conditions",
            "acceptance_criteria",
        }
        self.assertTrue(required.issubset(depth_modes.columns))
        executive = depth_modes[depth_modes["depth_mode"].isin(["depth_1_executive_brief", "depth_2_management_memo"])]
        self.assertTrue(executive["excluded_sections"].str.contains("full", case=False, regex=False).all())
        finance = depth_modes.loc[depth_modes["depth_mode"].eq("depth_3_finance_working_package")].iloc[0]
        self.assertIn("full evidence map", finance["included_sections"])
        self.assertIn("all memo slices", finance["included_sections"])
        operating = depth_modes.loc[depth_modes["depth_mode"].eq("depth_4_operating_model")].iloc[0]
        self.assertIn("owner", operating["included_sections"])
        self.assertIn("due date", operating["included_sections"])
        self.assertIn("status", operating["included_sections"])

    def test_signal_and_compact_profile_fields_exist(self) -> None:
        signal_catalog = pd.read_parquet(MART_ARTIFACTS["mart_signal_catalog_full"])
        compact = pd.read_parquet(MART_ARTIFACTS["mart_main_compact_executive_yoy_mom"])
        self.assertTrue(PROFILE_SIGNAL_FIELDS.issubset(signal_catalog.columns))
        self.assertTrue((PROFILE_SIGNAL_FIELDS - {"memo_section"}).issubset(compact.columns))

    def test_profile_readiness_and_preview_contract(self) -> None:
        readiness = pd.read_parquet(PROFILE_ARTIFACTS["profile_readiness_matrix"])
        preview = pd.read_parquet(PROFILE_ARTIFACTS["profile_preview_index"])
        self.assertEqual(len(readiness), 18)
        self.assertEqual(len(preview), 18)
        self.assertTrue(readiness["readiness_status"].isin({"ready", "partial", "blocked", "preview_only"}).all())
        self.assertTrue({"default_depth_mode", "ready_depth_modes", "partial_depth_modes", "blocked_depth_modes", "depth_mode_readiness"}.issubset(readiness.columns))
        self.assertTrue(preview["can_build_docx"].isin({"да", "нет"}).all())

    def test_no_docx_generated_by_mart_or_profile_tasks(self) -> None:
        # Legacy DOCX files may remain archived or present from old downstream,
        # but accepted MART/profile tasks must not generate or modify DOCX.
        self.assertEqual(self.profile_qa["docx_generated"], "no")
        self.assertTrue(self.profile_qa["checks"]["no_docx_reports_generated_or_modified"])

    def test_excel_visible_columns_are_russian_or_business_readable(self) -> None:
        for path, expected_sheets in EXCEL_ARTIFACTS.items():
            self.assertTrue(path.exists(), str(path))
            with pd.ExcelFile(path) as workbook:
                for sheet_name in expected_sheets:
                    self.assertIn(sheet_name, workbook.sheet_names)
                    headers = pd.read_excel(workbook, sheet_name=sheet_name, nrows=0).columns
                    snake_case_headers = [
                        header
                        for header in headers
                        if re.fullmatch(r"[a-z][a-z0-9_]*", str(header))
                        and "_" in str(header)
                    ]
                    forbidden_english_headers = [
                        header
                        for header in headers
                        if str(header)
                        in {
                            "Source files",
                            "Source rows",
                            "Source file",
                            "Source row ID",
                            "Month Dt",
                            "Stage In Out Eur",
                            "Sum Abs Mom Delta Eur",
                            "Month No",
                            "Sheet Block",
                            "ID evidence",
                            "Non-EUR сумма, EUR",
                        }
                    ]
                    self.assertFalse(snake_case_headers, f"{path.name}/{sheet_name}: {snake_case_headers}")
                    self.assertFalse(forbidden_english_headers, f"{path.name}/{sheet_name}: {forbidden_english_headers}")

    def test_management_excel_guardrails(self) -> None:
        with pd.ExcelFile(MARTS_DIR / "mart_full_package.xlsx") as workbook:
            self.assertNotIn("11_Юрлица_Валюты", workbook.sheet_names)
            for sheet_name, grain_columns in MANAGEMENT_SHEET_GRAINS.items():
                self.assertIn(sheet_name, workbook.sheet_names)
                headers = set(pd.read_excel(workbook, sheet_name=sheet_name, nrows=0).columns)
                self.assertTrue(set(grain_columns).issubset(headers), sheet_name)
                self.assertFalse({"Sheet Block", "Блок листа", "sheet_block"} & headers, sheet_name)
                self.assertFalse({"source_rows", "source_files", "Строки-источники", "Файлы-источники"} & headers, sheet_name)

    def test_stage_raw_and_mart_formula_preservation_checks_passed(self) -> None:
        self.assertTrue(RAW_DIR.exists())
        self.assertTrue(self.mart_qa["checks"]["raw_unchanged"])
        self.assertTrue(self.mart_qa["checks"]["stage_unchanged"])
        self.assertTrue(self.profile_qa["checks"]["raw_untouched"])
        self.assertTrue(self.profile_qa["checks"]["stage_untouched"])
        self.assertTrue(self.profile_qa["checks"]["mart_formulas_untouched"])

    def test_mart_and_profile_qa_reports_pass(self) -> None:
        self.assertEqual(self.mart_qa["qa_status"], "pass")
        self.assertEqual(self.profile_qa["qa_status"], "pass")
        for check_name in [
            "mart_main_full_budget_exists",
            "mart_flow_base_month_exists",
            "mart_signal_catalog_full_exists",
            "mart_main_compact_executive_yoy_mom_exists",
            "excel_workbook_has_russian_column_names",
            "legal_currency_old_mixed_sheet_removed",
            "legal_currency_split_sheets_exist",
            "legal_entity_sheet_single_grain",
            "currency_sheet_single_grain",
            "legal_entity_currency_sheet_single_grain",
            "eur_not_counted_as_non_eur_exposure",
            "in_ratios_not_shown_without_valid_scope",
            "excel_management_sheets_have_declared_grain",
            "excel_no_mixed_grain_sheet_names_or_markers",
            "excel_legal_currency_sheets_remain_split",
            "excel_management_sheets_have_no_long_lineage_dump",
            "excel_sheets_have_no_mixed_grain_structural_nulls",
            "in_ratios_have_denominator_status",
            "counterparty_execution_pct_not_misleading",
            "timing_sheet_candidate_only",
            "refunds_sheet_compact_and_refund_specific",
            "flow_rows_have_flow_yoy_metrics",
            "flow_rows_have_flow_mom_metrics",
            "flow_metrics_source_grain_present",
            "flow_metrics_not_joined_to_business_rows",
            "flow_yoy_metrics_match_flow_base",
            "flow_mom_metrics_match_flow_base",
            "regular_yoy_excludes_service_rows",
            "regular_yoy_business_metrics_unchanged",
            "main_full_pivot_safe_grain",
            "main_full_no_duplicate_keys",
            "main_full_yoy_calculated_at_pivot_grain",
            "main_full_mom_calculated_at_pivot_grain",
            "main_full_supports_user_pivot_hierarchy",
            "yoy_delta_equals_current_minus_prior_at_main_grain",
            "mom_delta_equals_current_minus_previous_at_main_grain",
            "row_level_evidence_sheet_preserved",
            "flow_metrics_preserved",
            "cutoff_checks_preserved",
            "row_level_evidence_sheet_is_row_level",
            "excel_no_duplicate_pivot_detail_sheets",
            "detailed_yoy_no_duplicate_keys",
            "detailed_mom_no_duplicate_keys",
            "detailed_yoy_calculated_at_counterparty_grain",
            "detailed_mom_calculated_at_counterparty_grain",
            "detailed_sheets_exclude_service_flow_rows",
            "pivot_safe_numerators_present",
            "ordinary_summary_sheets_preserved",
        ]:
            self.assertTrue(self.mart_qa["checks"][check_name], check_name)
        for check_name in [
            "all_18_profiles_exist",
            "r1_profiles_active",
            "profile_catalog_has_governance_fields",
            "profile_catalog_has_depth_mode_fields",
            "profile_readiness_has_depth_mode_fields",
            "all_4_depth_modes_exist",
            "profile_preview_mode",
            "excel_files_have_russian_visible_columns",
        ]:
            self.assertTrue(self.profile_qa["checks"][check_name], check_name)
        self.assertEqual(self.depth_modes_qa["qa_status"], "pass")
        for check_name in [
            "all_4_depth_modes_exist",
            "each_mode_has_included_excluded_sections",
            "each_mode_has_audience_and_artifact_policy",
            "executive_modes_do_not_include_full_evidence_dump",
            "finance_package_includes_evidence_and_slices",
            "operating_mode_includes_action_owner_due_status",
            "profile_catalog_has_default_allowed_depth_modes",
            "profile_readiness_has_depth_mode_readiness",
            "stage_untouched",
            "raw_untouched",
            "mart_formulas_untouched",
        ]:
            self.assertTrue(self.depth_modes_qa["checks"][check_name], check_name)

    def test_service_flow_rows_have_separate_flow_metrics(self) -> None:
        main = pd.read_parquet(MART_ARTIFACTS["mart_main_full_budget"])
        yoy = pd.read_parquet(MARTS_DIR / "slice_yoy_article_cfo_month.parquet")
        mom = pd.read_parquet(MARTS_DIR / "slice_mom_article_cfo_month.parquet")
        service_values = {"IN", "OUT", "IN-OUT"}
        service = main[main["row_role"].eq("service_flow_row") & main["article"].isin(service_values)]
        business = main[~main["row_role"].eq("service_flow_row")]
        self.assertFalse(service.empty)
        self.assertTrue(service["article"].isin(service_values).all())
        self.assertFalse(yoy["article"].isin(service_values).any())
        self.assertFalse(mom["article"].isin(service_values).any())
        self.assertTrue(service["flow_yoy_source_slice"].eq("mart_flow_base_month").all())
        self.assertTrue(service["flow_mom_source_slice"].eq("mart_flow_base_month").all())
        self.assertTrue(service["flow_yoy_metric_grain"].eq("flow_metric+month").all())
        self.assertTrue(service["flow_mom_metric_grain"].eq("flow_metric+month").all())
        self.assertTrue(service["yoy_source_slice"].eq("mart_flow_base_month").all())
        self.assertTrue(service["mom_source_slice"].eq("mart_flow_base_month").all())
        self.assertTrue(service["yoy_metric_grain"].eq("flow_metric+month").all())
        self.assertTrue(service["mom_metric_grain"].eq("flow_metric+month").all())
        self.assertTrue(service["prior_year_fact_eur"].equals(service["flow_prior_year_value_eur"]))
        self.assertTrue(service["previous_month_fact_eur"].equals(service["flow_previous_month_value_eur"]))
        self.assertTrue((service["yoy_delta_eur"] - (service["fact_eur"] - service["prior_year_fact_eur"].fillna(0))).abs().le(0.01).all())
        self.assertTrue((service["mom_delta_eur"] - (service["fact_eur"] - service["previous_month_fact_eur"].fillna(0))).abs().le(0.01).all())
        flow_cols = [
            "flow_prior_year_value_eur",
            "flow_yoy_delta_eur",
            "flow_abs_yoy_delta_eur",
            "flow_yoy_pct",
            "flow_previous_month_value_eur",
            "flow_mom_delta_eur",
            "flow_abs_mom_delta_eur",
            "flow_mom_pct",
            "flow_yoy_source_slice",
            "flow_mom_source_slice",
        ]
        self.assertTrue(business[flow_cols].isna().all().all())

    def test_main_full_mart_is_pivot_safe_at_user_grain(self) -> None:
        main = pd.read_parquet(MART_ARTIFACTS["mart_main_full_budget"])
        self.assertTrue(set(PIVOT_SAFE_MAIN_GRAIN).issubset(main.columns))
        self.assertNotIn("counterparty_key", main.columns)
        self.assertFalse(main.duplicated(PIVOT_SAFE_MAIN_GRAIN).any())
        required_metrics = {
            "plan_eur",
            "fact_eur",
            "delta_eur",
            "abs_delta_eur",
            "prior_year_fact_eur",
            "yoy_delta_eur",
            "abs_yoy_delta_eur",
            "yoy_pct",
            "previous_month_fact_eur",
            "mom_delta_eur",
            "abs_mom_delta_eur",
            "mom_pct",
            "planning_risk_flag",
            "planning_risk",
            "yoy_pct_numerator_eur",
            "yoy_pct_denominator_eur",
            "mom_pct_numerator_eur",
            "mom_pct_denominator_eur",
            "execution_pct_numerator_eur",
            "execution_pct_denominator_eur",
        }
        self.assertTrue(required_metrics.issubset(main.columns))
        expected_sort_values = {
            "IN": "00_IN",
            "OUT": "00_OUT",
            "IN-OUT": "00_IN-OUT",
            "FIX": "01_FIX",
            "PROJECT&DEPARTMENT SERVICES": "02_PROJECT&DEPARTMENT SERVICES",
            "INVEST": "03_INVEST",
            "FIN SERVICES": "04_FIN SERVICES",
            "OTHER OUTFLOWS": "05_OTHER OUTFLOWS",
        }
        self.assertIn("article_type_sort", main.columns)
        actual_sort_values = main.groupby("article_type", dropna=False)["article_type_sort"].first().to_dict()
        for article_type, expected in expected_sort_values.items():
            self.assertEqual(actual_sort_values.get(article_type), expected)
        business = main[~main["row_role"].eq("service_flow_row")]
        yoy_rows = business[["fact_eur", "prior_year_fact_eur", "yoy_delta_eur"]].dropna(subset=["fact_eur", "yoy_delta_eur"])
        mom_rows = business[["fact_eur", "previous_month_fact_eur", "mom_delta_eur"]].dropna(subset=["fact_eur", "mom_delta_eur"])
        self.assertFalse(yoy_rows.empty)
        self.assertFalse(mom_rows.empty)
        self.assertTrue((yoy_rows["yoy_delta_eur"] - (yoy_rows["fact_eur"] - yoy_rows["prior_year_fact_eur"].fillna(0))).abs().le(0.01).all())
        self.assertTrue((mom_rows["mom_delta_eur"] - (mom_rows["fact_eur"] - mom_rows["previous_month_fact_eur"].fillna(0))).abs().le(0.01).all())

    def test_working_counterparty_slices_do_not_use_counterparty_key(self) -> None:
        for name in [
            "slice_plan_fact_article_cfo_counterparty_month",
            "slice_plan_fact_counterparty",
            "slice_yoy_counterparty",
            "slice_mom_counterparty",
            "slice_plan_vs_history_counterparty",
            "slice_localization_article_cfo_counterparty",
            "slice_counterparty_concentration",
        ]:
            df = pd.read_parquet(MARTS_DIR / f"{name}.parquet")
            self.assertNotIn("counterparty_key", df.columns, name)

    def test_pivot_safe_excel_sheets_are_preserved(self) -> None:
        with pd.ExcelFile(MARTS_DIR / "mart_full_package.xlsx") as workbook:
            for sheet_name in [
                "01_Полный_MART",
                "22_Полный_MART_Строки",
            ]:
                self.assertIn(sheet_name, workbook.sheet_names)
            for sheet_name in ["18_PlanFact_Детально", "19_YoY_Детально", "20_MoM_Детально", "21_ПланРиск_Детально"]:
                self.assertNotIn(sheet_name, workbook.sheet_names)
            headers = set(pd.read_excel(workbook, sheet_name="01_Полный_MART", nrows=0).columns)
            counterparty_headers = set(pd.read_excel(workbook, sheet_name="10_Контрагенты", nrows=0).columns)
            row_headers = set(pd.read_excel(workbook, sheet_name="22_Полный_MART_Строки", nrows=0).columns)
        required_headers = {
            "Месяц",
            "Год",
            "Тип периода",
            "Тип статьи",
            "Тип статьи сортировка",
            "Статья 1",
            "Статья 2",
            "Статья",
            "ЦФО",
            "Контрагент",
            "Числитель YoY %, EUR",
            "Знаменатель YoY %, EUR",
            "Числитель MoM %, EUR",
            "Знаменатель MoM %, EUR",
            "Числитель исполнения, EUR",
            "Знаменатель исполнения, EUR",
        }
        self.assertTrue(required_headers.issubset(headers))
        self.assertNotIn("Ключ контрагента", headers)
        self.assertNotIn("Ключ контрагента", counterparty_headers)
        self.assertIn("Ключ контрагента", row_headers)

    def test_chart_package_contract_when_present(self) -> None:
        if self.chart_qa is None:
            self.skipTest("Chart package has not been generated for this workspace.")
        self.assertEqual(self.chart_qa["qa_status"], "pass")
        catalog = pd.read_parquet(CHARTS_DIR / "chart_catalog.parquet")
        self.assertTrue(CHART_REQUIRED_IDS.issubset(set(catalog["chart_id"])))
        self.assertTrue(catalog[["source_mart", "source_slice", "metric", "grain", "period", "limitation"]].fillna("").ne("").all().all())
        self.assertTrue(catalog[["chart_role", "chart_order", "recommended_placement", "caption_ru"]].fillna("").ne("").all().all())
        self.assertTrue(catalog["chart_role"].isin({"executive_body", "appendix", "qa_only"}).all())
        self.assertTrue(catalog["chart_order"].is_monotonic_increasing)
        for row in catalog.to_dict("records"):
            self.assertTrue((PROJECT_ROOT / row["data_path"]).exists(), row["chart_id"])
            self.assertTrue((PROJECT_ROOT / row["image_path"]).exists(), row["chart_id"])
        for check_name in [
            "no_chart_reads_raw_or_stage",
            "service_rows_excluded_from_expense_deviation_charts",
            "in_ratio_charts_use_valid_denominator_status",
            "planning_risk_labeled_future_risk_not_actual_execution",
            "yoy_chart_does_not_use_missing_base_as_strong_conclusion",
            "excel_visible_columns_are_russian",
            "chart_images_generated",
            "chart_images_readable_dimensions",
            "each_chart_has_role_order_placement_caption",
            "chart_catalog_order_matches_executive_route",
            "executive_body_charts_cover_memo_route",
            "no_docx_generated",
            "raw_untouched",
            "stage_untouched",
            "mart_formulas_untouched",
            "no_long_lineage_in_chart_datasets",
        ]:
            self.assertTrue(self.chart_qa["checks"][check_name], check_name)

    def test_report_contract_when_present(self) -> None:
        if self.report_contract_qa is None:
            self.skipTest("Report contract has not been generated for this workspace.")
        self.assertEqual(self.report_contract_qa["qa_status"], "pass")
        # Report artifacts were reorganized under 01_executive_yoy_mom_budget_memo/source_refs as part of the
        # 18-memo report factory layout. The legacy root-level files are archived.
        self.assertTrue((MEMO_01_SOURCE_REFS_DIR / "memo_01__executive_yoy_mom_budget_memo__2026-05-21__report_contract.md").exists())
        self.assertTrue((MEMO_01_SOURCE_REFS_DIR / "memo_01__executive_yoy_mom_budget_memo__2026-05-21__report_contract.json").exists())
        self.assertTrue((MEMO_01_SOURCE_REFS_DIR / "memo_01__executive_yoy_mom_budget_memo__2026-05-21__section_map.xlsx").exists())
        self.assertTrue((MEMO_01_SOURCE_REFS_DIR / "memo_01__executive_yoy_mom_budget_memo__2026-05-21__claim_plan.xlsx").exists())
        self.assertTrue((MEMO_01_SOURCE_REFS_DIR / "memo_01__executive_yoy_mom_budget_memo__2026-05-21__chart_placement.xlsx").exists())
        for check_name in [
            "all_12_sections_exist",
            "section_order_correct",
            "each_section_has_source_or_documented_reason",
            "each_section_has_evidence_requirement",
            "each_section_has_limitation_rule",
            "executive_body_charts_1_8",
            "appendix_charts_9_10",
            "planning_risk_marked_future_not_execution",
            "yoy_and_mom_separate_sections",
            "in_context_included",
            "raw_untouched",
            "stage_untouched",
            "mart_formulas_untouched",
            "chart_data_untouched",
            "no_docx_generated_or_modified",
        ]:
            self.assertTrue(self.report_contract_qa["checks"][check_name], check_name)

    def test_draft_data_package_when_present(self) -> None:
        if self.draft_package_qa is None:
            self.skipTest("Draft data package has not been generated for this workspace.")
        self.assertEqual(self.draft_package_qa["qa_status"], "pass")
        for path in [
            LLM_DIR / "executive_yoy_mom_draft_data_package.json",
            LLM_DIR / "executive_yoy_mom_draft_data_package.md",
            LLM_DIR / "executive_yoy_mom_section_inputs.xlsx",
            LLM_DIR / "executive_yoy_mom_claim_candidates.xlsx",
            LLM_DIR / "executive_yoy_mom_evidence_map.xlsx",
            LLM_DIR / "executive_yoy_mom_chart_refs.xlsx",
        ]:
            self.assertTrue(path.exists(), str(path))
        package = json.loads((LLM_DIR / "executive_yoy_mom_draft_data_package.json").read_text(encoding="utf-8"))
        self.assertEqual(len(package["sections"]), 12)
        self.assertGreater(len(package["claim_candidates"]), 0)
        for check_name in [
            "section_inputs_all_12_sections",
            "claim_candidates_have_evidence_and_source_fields",
            "chart_refs_match_catalog",
            "evidence_map_covers_claims",
            "planning_risk_not_actual_execution",
            "yoy_and_mom_separated",
            "in_context_claims_have_valid_denominator_status",
            "no_final_prose_generated",
            "no_docx_generated",
            "raw_untouched",
            "stage_untouched",
            "mart_untouched",
            "charts_untouched",
        ]:
            self.assertTrue(self.draft_package_qa["checks"][check_name], check_name)

    def test_controlled_draft_memo_when_present(self) -> None:
        if self.controlled_draft_qa is None:
            self.skipTest("Controlled draft memo has not been generated for this workspace.")
        self.assertEqual(self.controlled_draft_qa["qa_status"], "pass")
        for path in [
            MEMO_01_DRAFT_DIR / "memo_01__executive_yoy_mom_budget_memo__2026-05-21__controlled_draft.md",
            MEMO_01_DRAFT_DIR / "memo_01__executive_yoy_mom_budget_memo__2026-05-21__controlled_draft.json",
        ]:
            self.assertTrue(path.exists(), str(path))
        draft = json.loads((MEMO_01_DRAFT_DIR / "memo_01__executive_yoy_mom_budget_memo__2026-05-21__controlled_draft.json").read_text(encoding="utf-8"))
        self.assertEqual(len(draft["sections"]), 12)
        for section in draft["sections"]:
            self.assertEqual(
                set(section["mvp_blocks"]),
                {"facts", "calculations", "interpretations", "recommendations", "hypotheses", "limitations"},
            )
        for check_name in [
            "all_12_sections_exist",
            "all_sections_have_mvp_blocks",
            "claim_categories_are_separated",
            "stop_conditions_applied",
            "low_confidence_not_final_fact",
            "risk_claims_have_risk_basis",
            "recommendations_require_owner_due_status",
            "limitations_visible",
            "planning_risk_future_not_actual_execution",
            "yoy_and_mom_sections_separated",
            "no_docx_generated",
            "raw_untouched",
            "stage_untouched",
            "mart_untouched",
            "charts_untouched",
            "production_readiness_not_claimed",
        ]:
            self.assertTrue(self.controlled_draft_qa["checks"][check_name], check_name)

    def test_executive_yoy_mom_memo_draft_when_present(self) -> None:
        if self.memo_draft_qa is None:
            self.skipTest("Executive YoY/MoM memo draft has not been generated for this workspace.")
        self.assertEqual(self.memo_draft_qa["qa_status"], "pass")
        draft_path = MEMO_01_DRAFT_DIR / "memo_01__executive_yoy_mom_budget_memo__2026-05-21__draft.md"
        self.assertTrue(draft_path.exists(), str(draft_path))
        memo_text = draft_path.read_text(encoding="utf-8")
        expected_sections = [
            "Рамка анализа",
            "Executive Summary",
            "Как читать записку",
            "Исторический факт: масштаб Plan-Fact",
            "YoY: сдвиг уровня к прошлому году",
            "MoM: помесячная динамика и нестабильность",
            "Локализация: статья × ЦФО",
            "Плановый риск: план к исторической базе",
            "iGaming flow context: отклонения к IN",
            "QC и ограничения",
            "Реестр приоритетных проверок",
            "Итоговый вывод",
        ]
        self.assertEqual([line[3:] for line in memo_text.splitlines() if line.startswith("## ")], expected_sections)
        self.assertIn("[DATA FACT]", memo_text)
        self.assertIn("[INTERPRETATION]", memo_text)
        self.assertIn("[LIMITATION]", memo_text)
        self.assertIn("Evidence: ", memo_text)
        self.assertIn("Source: ", memo_text)
        self.assertIn("Metric: ", memo_text)
        for check_name in [
            "all_12_sections_exist",
            "important_paragraphs_have_claim_labels",
            "important_paragraphs_have_evidence_source_metric",
            "evidence_refs_are_known",
            "source_refs_are_known",
            "metric_refs_are_known",
            "chart_refs_exist",
            "executive_body_charts_1_8_referenced",
            "yoy_and_mom_separate",
            "planning_risk_not_fact_execution",
            "in_context_explains_proportionality",
            "no_timing_confirmed_claim",
            "risk_has_risk_basis",
            "low_confidence_not_final_fact",
            "limitations_visible",
            "no_unsupported_refs",
            "no_docx_generated",
            "raw_untouched",
            "stage_untouched",
            "mart_untouched",
            "charts_untouched",
        ]:
            self.assertTrue(self.memo_draft_qa["checks"][check_name], check_name)


if __name__ == "__main__":
    unittest.main()
