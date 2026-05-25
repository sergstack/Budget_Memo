from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.main import (
    AUDIT_DIR,
    DIAGNOSTIC_OUTPUTS,
    FULL_STAGE_OUTPUT,
    OLD_DIAGNOSTIC_OUTPUTS,
    OLD_USER_OUTPUTS,
    build_full_stage,
    load_cons_budget,
    run_pipeline,
)


ALLOWED_SOURCE_MIX = {
    "plan_only",
    "fact_only",
    "plan_and_fact",
    "p_fact_adjusted",
    "mixed",
    "refund_only",
    "refund_mixed",
    "cons_budget",
}

EXPECTED_COLUMNS = [
    "Месяц",
    "Дата",
    "Тип периода",
    "source_mix",
    "included_in_reconciliation",
    "has_plan",
    "has_fact",
    "has_p_fact_adjustment",
    "has_player_refund",
    "Код статьи ДДС",
    "Тип",
    "Статья 1",
    "Статья 2",
    "Статья",
    "ЦФО",
    "Юр. лицо",
    "Контрагент",
    "Ключ контрагента",
    "Тип контрагента",
    "Валюта",
    "Сумма исходная",
    "План, EUR",
    "Факт, EUR",
    "IN-OUT, EUR",
    "source_file",
    "source_row_id",
]


class FullStageContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_pipeline(write_outputs=True)
        cls.stage = pd.read_csv(FULL_STAGE_OUTPUT, sep=";", decimal=",", dtype={"source_row_id": str})

    def test_expected_stage_outputs_exist(self) -> None:
        self.assertTrue(Path(FULL_STAGE_OUTPUT).exists())
        self.assertTrue(AUDIT_DIR.exists())
        for old_output in OLD_USER_OUTPUTS:
            self.assertFalse(Path(old_output).exists())
        for old_output in OLD_DIAGNOSTIC_OUTPUTS:
            self.assertFalse(Path(old_output).exists())
        root_csv_files = sorted(path.name for path in FULL_STAGE_OUTPUT.parent.glob("*.csv"))
        audit_csv_files = sorted(path.name for path in AUDIT_DIR.glob("*.csv"))
        self.assertEqual(root_csv_files, ["01_full_stage.csv"])
        self.assertEqual(audit_csv_files, sorted(path.name for path in DIAGNOSTIC_OUTPUTS.values()))

    def test_required_columns_only(self) -> None:
        self.assertEqual(list(self.stage.columns), EXPECTED_COLUMNS)
        forbidden = {
            "Тип операции",
            "Источник данных",
            "Направление",
            "Статья 3",
            "План - Факт, EUR",
            "ABS отклонения, EUR",
            "% исполнения бюджета",
            "Направление отклонения",
            "IN, EUR",
            "OUT, EUR",
            "Доля от IN-OUT, %",
            "Доля от IN, %",
            "Доля от OUT, %",
            "MoM",
            "YoY",
        }
        self.assertFalse(forbidden.intersection(self.stage.columns))

    def test_csv_round_trip_parser_contract(self) -> None:
        parsed = pd.read_csv(FULL_STAGE_OUTPUT, sep=";", decimal=",", encoding="utf-8-sig", dtype={"source_row_id": str})
        self.assertEqual(list(parsed.columns), EXPECTED_COLUMNS)
        self.assertGreater(len(parsed), 0)
        self.assertEqual(len(parsed), 42217)
        self.assertEqual(len(parsed.columns), 26)
        with Path(FULL_STAGE_OUTPUT).open("r", encoding="utf-8-sig") as handle:
            physical_lines = sum(1 for _ in handle)
        self.assertEqual(physical_lines, len(parsed) + 1)

    def test_qa_data_contract_notes(self) -> None:
        parsed = pd.read_csv(
            FULL_STAGE_OUTPUT,
            sep=";",
            decimal=",",
            encoding="utf-8-sig",
            dtype={
                "Ключ контрагента": "string",
                "source_row_id": "string",
                "Код статьи ДДС": "string",
            },
        )
        pd.to_datetime(parsed["Дата"], format="%Y-%m-%d", errors="raise")
        for col in ["Ключ контрагента", "source_row_id", "Код статьи ДДС"]:
            self.assertTrue(pd.api.types.is_string_dtype(parsed[col]))
        for col in ["План, EUR", "Факт, EUR", "IN-OUT, EUR", "Сумма исходная"]:
            self.assertTrue(pd.api.types.is_numeric_dtype(parsed[col]))

        cons_rows = parsed[parsed["source_mix"].eq("cons_budget")]
        expense_rows = parsed[parsed["source_mix"].ne("cons_budget")]
        self.assertFalse(cons_rows.empty)
        self.assertFalse(expense_rows.empty)
        self.assertTrue(cons_rows["included_in_reconciliation"].eq(0).all())
        self.assertEqual(cons_rows.groupby("Месяц")["Статья"].nunique().min(), 3)
        self.assertEqual(cons_rows.groupby("Месяц")["Статья"].nunique().max(), 3)
        self.assertLessEqual(parsed.groupby("Месяц")["IN-OUT, EUR"].nunique(dropna=False).max(), 1)
        self.assertIn("Сумма исходная", parsed.columns)
        self.assertNotIn("Сумма исходная", self.result["reconciliation"].columns)

    def test_diagnostic_outputs_contract(self) -> None:
        expected_layers = {
            "p_fact": "p_fact",
            "budget_rows": "budget_rows",
            "dds": "dds",
            "p_fact_adjustments": "p_fact_adjustment",
            "cons_budget": "cons_budget",
        }
        for name, path in DIAGNOSTIC_OUTPUTS.items():
            self.assertTrue(path.exists(), path.name)
            parsed = pd.read_csv(path, sep=";", decimal=",", encoding="utf-8-sig")
            self.assertGreater(len(parsed), 0, path.name)
            self.assertIn("source_layer", parsed.columns)
            self.assertEqual(set(parsed["source_layer"]), {expected_layers[name]})

            dtype = {
                col: "string"
                for col in ["Код статьи ДДС", "Ключ контрагента", "source_row_id"]
                if col in parsed.columns
            }
            parsed_with_keys = pd.read_csv(path, sep=";", decimal=",", encoding="utf-8-sig", dtype=dtype)
            for col in dtype:
                self.assertTrue(pd.api.types.is_string_dtype(parsed_with_keys[col]), f"{path.name}:{col}")

    def test_cons_budget_diagnostic_output(self) -> None:
        cons = pd.read_csv(
            DIAGNOSTIC_OUTPUTS["cons_budget"],
            sep=";",
            decimal=",",
            encoding="utf-8-sig",
            dtype={"source_row_id": "string"},
        )
        self.assertEqual(len(cons), 72)
        self.assertEqual(set(cons["Статья"]), {"IN", "OUT", "IN-OUT"})
        counts = cons.groupby("Месяц")["Статья"].nunique()
        self.assertTrue(counts.eq(3).all())
        self.assertNotIn("source_layer", self.result["reconciliation"].columns)
        self.assertNotIn("source_mix", self.result["reconciliation"].columns)

    def test_allowed_values(self) -> None:
        self.assertTrue(self.stage["Месяц"].astype(str).str.match(r"^\d{4}-\d{2}$").all())
        self.assertFalse(self.stage["Месяц"].isna().any())
        self.assertTrue(set(self.stage["Тип периода"]).issubset({"historical", "planning"}))
        self.assertTrue(set(self.stage["source_mix"]).issubset(ALLOWED_SOURCE_MIX))
        self.assertTrue(set(self.stage["has_plan"]).issubset({0, 1}))
        self.assertTrue(set(self.stage["has_fact"]).issubset({0, 1}))
        self.assertTrue(set(self.stage["has_p_fact_adjustment"]).issubset({0, 1}))
        self.assertTrue(set(self.stage["has_player_refund"]).issubset({0, 1}))
        self.assertTrue(set(self.stage["included_in_reconciliation"]).issubset({0, 1}))
        self.assertFalse(self.stage["Код статьи ДДС"].isna().any())
        self.assertFalse(self.stage["ЦФО"].isna().any())
        self.assertFalse(self.stage["source_file"].isna().any())
        self.assertFalse(self.stage["source_row_id"].isna().any())
        non_cons = self.stage[self.stage["source_mix"].ne("cons_budget")]
        self.assertFalse(non_cons["План, EUR"].isna().any())
        self.assertFalse(non_cons["Факт, EUR"].isna().any())
        self.assertLessEqual(self.stage.groupby("Месяц")["IN-OUT, EUR"].nunique(dropna=False).max(), 1)

    def test_dates_are_populated_and_formatted(self) -> None:
        self.assertFalse(self.stage["Дата"].isna().any())
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(self.stage["Дата"].astype(str).map(lambda value: bool(date_pattern.match(value))).all())
        adjustments = self.stage[self.stage["has_p_fact_adjustment"].eq(1)]
        self.assertTrue(adjustments["Дата"].eq(adjustments["Месяц"].astype(str) + "-01").all())

    def test_cons_budget_service_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cons_budget = load_cons_budget(Path(tmp_dir))
        cons_months = set(cons_budget["Месяц"].astype(str))
        service = self.stage[self.stage["source_mix"].eq("cons_budget")]
        self.assertEqual(set(service["Месяц"].astype(str)), cons_months)
        counts = service.groupby("Месяц")["Код статьи ДДС"].nunique()
        self.assertTrue(counts.eq(3).all())
        for metric in ["IN", "OUT", "IN-OUT"]:
            rows = service[service["Код статьи ДДС"].eq(metric)]
            self.assertFalse(rows.empty)
            self.assertTrue(rows["Тип"].eq(metric).all())
            self.assertTrue(rows["Статья 1"].eq(metric).all())
            self.assertTrue(rows["Статья 2"].eq(metric).all())
            self.assertTrue(rows["Статья"].eq(metric).all())
            self.assertTrue(rows["ЦФО"].eq(metric).all())
            self.assertTrue(rows["Юр. лицо"].eq("not_applicable").all())
            self.assertTrue(rows["Контрагент"].eq(metric).all())
            self.assertTrue(rows["Ключ контрагента"].eq(metric).all())
            self.assertTrue(rows["Тип контрагента"].eq("not_applicable").all())
            self.assertTrue(rows["Валюта"].eq("EUR").all())
            self.assertTrue(rows["included_in_reconciliation"].eq(0).all())
            self.assertTrue(rows["has_p_fact_adjustment"].eq(0).all())
            self.assertTrue(rows["has_player_refund"].eq(0).all())
        inout_service = service[service["Код статьи ДДС"].eq("IN-OUT")][["Месяц", "Факт, EUR"]]
        expected = dict(zip(inout_service["Месяц"], inout_service["Факт, EUR"]))
        for month, value in expected.items():
            month_rows = self.stage[self.stage["Месяц"].eq(month)]
            if pd.isna(value):
                self.assertTrue(month_rows["IN-OUT, EUR"].isna().all())
            else:
                self.assertTrue(month_rows["IN-OUT, EUR"].eq(value).all())

    def test_p_fact_adjustment_policies(self) -> None:
        adjustments = self.stage[self.stage["has_p_fact_adjustment"].eq(1)]
        self.assertFalse(adjustments.empty)
        self.assertTrue(adjustments["source_mix"].eq("p_fact_adjusted").all())
        self.assertTrue(adjustments["Юр. лицо"].eq("not_applicable").all())
        self.assertTrue(adjustments["Тип контрагента"].eq("not_applicable").all())
        self.assertTrue(adjustments["Контрагент"].eq("p-fact").all())
        self.assertTrue(adjustments["Ключ контрагента"].eq("p_fact").all())
        self.assertTrue(adjustments["Валюта"].eq("EUR").all())
        self.assertTrue(adjustments["source_file"].eq("p-fact").all())

    def test_counterparty_key_normalization(self) -> None:
        keyed = self.stage[self.stage["Ключ контрагента"].ne("unknown") & self.stage["Ключ контрагента"].ne("p_fact")]
        self.assertFalse(keyed.empty)
        self.assertFalse(keyed["Контрагент"].astype(str).str.contains(r"\s/\s*\S+\s*$", regex=True).any())
        missing = self.stage[self.stage["Контрагент"].eq("Контрагент не указан")]
        self.assertFalse(missing.empty)
        self.assertTrue(missing["Ключ контрагента"].eq("unknown").all())

    def test_stage_keeps_plan_fact_adjustment_and_refund_rows(self) -> None:
        self.assertTrue((self.stage["has_plan"].eq(1) & self.stage["Факт, EUR"].eq(0)).any())
        self.assertTrue((self.stage["has_fact"].eq(1) & self.stage["План, EUR"].eq(0)).any())
        self.assertTrue(self.stage["has_p_fact_adjustment"].eq(1).any())
        refunds = self.stage[self.stage["has_player_refund"].eq(1)]
        self.assertFalse(refunds.empty)
        self.assertTrue(refunds["source_mix"].isin(["refund_only", "refund_mixed"]).all())
        self.assertTrue(refunds["included_in_reconciliation"].eq(0).all())

    def test_reconciliation_metrics(self) -> None:
        self.assertEqual(self.result["reconciliation_failed_pairs"], 0)
        self.assertGreater(self.result["total_reconciliation_pairs"], 0)
        self.assertLessEqual(self.result["max_abs_plan_diff"], 0.01)
        self.assertLessEqual(self.result["max_abs_fact_diff"], 0.01)
        self.assertNotIn("Контрагент", self.result["reconciliation"].columns)
        self.assertNotIn("Ключ контрагента", self.result["reconciliation"].columns)
        self.assertNotIn("Дата", self.result["reconciliation"].columns)
        self.assertNotIn("Сумма исходная", self.result["reconciliation"].columns)

    def test_synthetic_aggregation_rules(self) -> None:
        article_ref = pd.DataFrame(
            [
                {
                    "Код статьи ДДС": "CF0000001",
                    "Тип статьи": "FIX",
                    "Направление": "outflow",
                    "Статья 1": "A",
                    "Статья 2": "B",
                    "Статья": "C",
                }
            ]
        )
        base = {
            "Месяц": "2026-03",
            "Дата": "2026-03-05",
            "Тип периода": "planning",
            "Источник данных": "budget_rows",
            "ЦФО": "CFO",
            "Код статьи ДДС": "CF0000001",
            "Статья ДДС": "C",
            "Юр. лицо": "Entity",
            "Контрагент": "Vendor / 1234",
            "Тип контрагента": "unknown",
            "Валюта": "EUR",
            "Сумма исходная": 0.0,
            "included_in_reconciliation": 1,
            "is_player_refund": 0,
            "source_file": "source.xlsx",
            "source_row_id": "1",
        }
        union = pd.DataFrame(
            [
                {**base, "Тип операции": "План", "Сумма (план)": 100.0, "Сумма (факт)": 0.0},
                {
                    **base,
                    "Контрагент": "Vendor",
                    "Источник данных": "dds",
                    "Тип операции": "Факт",
                    "Сумма (план)": 0.0,
                    "Сумма (факт)": 80.0,
                    "source_row_id": "2",
                },
                {
                    **base,
                    "Дата": "2026-03-07",
                    "Контрагент": "Vendor",
                    "Источник данных": "dds",
                    "Тип операции": "Факт",
                    "Сумма (план)": 0.0,
                    "Сумма (факт)": 20.0,
                    "source_row_id": "3",
                },
                {
                    **base,
                    "Контрагент": "Other Vendor / 9999",
                    "Источник данных": "dds",
                    "Тип операции": "Факт",
                    "Сумма (план)": 0.0,
                    "Сумма (факт)": 10.0,
                    "source_row_id": "4",
                },
                {
                    **base,
                    "Контрагент": "No Plan Vendor",
                    "Источник данных": "dds",
                    "Тип операции": "Факт",
                    "Сумма (план)": 0.0,
                    "Сумма (факт)": 30.0,
                    "source_row_id": "5",
                },
                {
                    **base,
                    "Контрагент": "Ambiguous Vendor / 1111",
                    "Тип операции": "План",
                    "Сумма (план)": 40.0,
                    "Сумма (факт)": 0.0,
                    "source_row_id": "6",
                },
                {
                    **base,
                    "Контрагент": "Ambiguous Vendor / 2222",
                    "Тип операции": "План",
                    "Сумма (план)": 50.0,
                    "Сумма (факт)": 0.0,
                    "source_row_id": "7",
                },
                {
                    **base,
                    "Контрагент": "Ambiguous Vendor",
                    "Источник данных": "dds",
                    "Тип операции": "Факт",
                    "Сумма (план)": 0.0,
                    "Сумма (факт)": 60.0,
                    "source_row_id": "8",
                },
            ]
        )
        cons_budget = pd.DataFrame(
            [
                {"Месяц": "2026-03", "metric": "IN", "План, EUR": 1000.0, "Факт, EUR": 900.0},
                {"Месяц": "2026-03", "metric": "OUT", "План, EUR": 700.0, "Факт, EUR": 600.0},
                {"Месяц": "2026-03", "metric": "IN-OUT", "План, EUR": 300.0, "Факт, EUR": 300.0},
            ]
        )
        stage = build_full_stage(union, article_ref, cons_budget, {"2026-03"})
        combined = stage[stage["source_mix"].eq("plan_and_fact")]
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined.iloc[0]["Контрагент"], "Vendor")
        self.assertEqual(str(combined.iloc[0]["Ключ контрагента"]), "1234")
        self.assertEqual(combined.iloc[0]["План, EUR"], 100.0)
        self.assertEqual(combined.iloc[0]["Факт, EUR"], 80.0)
        self.assertTrue((stage["Дата"].eq("2026-03-07") & stage["source_mix"].eq("fact_only")).any())
        self.assertTrue((stage["Ключ контрагента"].eq("9999") & stage["source_mix"].eq("fact_only")).any())
        no_plan = stage[stage["Контрагент"].eq("No Plan Vendor")]
        self.assertEqual(str(no_plan.iloc[0]["Ключ контрагента"]), "unknown")
        ambiguous = stage[stage["Контрагент"].eq("Ambiguous Vendor")]
        self.assertTrue((ambiguous["Ключ контрагента"].eq("unknown") & ambiguous["source_mix"].eq("fact_only")).any())
        ambiguous_plan = ambiguous[ambiguous["source_mix"].eq("plan_only")]
        self.assertEqual(set(ambiguous_plan["Ключ контрагента"].astype(str)), {"1111", "2222"})


if __name__ == "__main__":
    unittest.main()
