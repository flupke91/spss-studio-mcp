"""P3: verify every analysis method against the real SPSS engine.

Runs each spss_* analysis tool on the example datasets and records whether it
completes and hits an expected output marker.  Results are printed as a table
and saved to ``docs/method_verification.json``.

Usage:
    python scripts/method_verification.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

from spss_mcp import server
from spss_mcp.spss_engine import get_engine

EX = Path(__file__).resolve().parents[1] / "examples" / "data"
OUT = Path(__file__).resolve().parents[1] / "docs" / "method_verification.json"

Q1_12 = [f"q{i}" for i in range(1, 13)]


def survey(p: str) -> str:
    return str(EX / "survey_study.sav")


def experiment(p: str) -> str:
    return str(EX / "experiment_study.sav")


def survival(p: str) -> str:
    return str(EX / "survival_study.sav")


def mediation(p: str) -> str:
    return str(EX / "mediation_study.sav")


def long_data(p: str) -> str:
    return str(EX / "long_study.sav")


CASES = [
    # (name, tool, kwargs, marker, data loader)
    (
        "descriptives",
        "spss_descriptives",
        dict(variables=["engagement_total", "cognitive", "affective", "behavioral"]),
        "Descriptive Statistics",
        survey,
    ),
    (
        "frequencies",
        "spss_frequencies",
        dict(variables=["gender", "major"]),
        "Statistics",
        survey,
    ),
    (
        "correlations",
        "spss_correlations",
        dict(variables=["cognitive", "affective", "behavioral"]),
        "Correlations",
        survey,
    ),
    (
        "crosstabs",
        "spss_crosstabs",
        dict(row_variable="gender", column_variable="major"),
        "Chi-Square",
        survey,
    ),
    (
        "normality_outliers",
        "spss_normality_outliers",
        dict(variables=["engagement_total"]),
        "Tests of Normality",
        survey,
    ),
    (
        "reliability_alpha",
        "spss_reliability_alpha",
        dict(variables=Q1_12),
        "Reliability Statistics",
        survey,
    ),
    (
        "factor",
        "spss_factor",
        dict(variables=Q1_12),
        "Total Variance Explained",
        survey,
    ),
    (
        "compute_scale_score",
        "spss_compute_scale_score",
        dict(new_variable="engagement_mean", items=Q1_12, method="mean"),
        "Descriptives",
        survey,
    ),
    (
        "glm_univariate",
        "spss_glm_univariate",
        dict(dependent="engagement_total", factors=["gender", "major"]),
        "Between-Subjects",
        survey,
    ),
    (
        "cluster_hierarchical",
        "spss_cluster_hierarchical",
        dict(variables=Q1_12, dendrogram=False),
        "Agglomeration",
        survey,
    ),
    (
        "twostep_cluster",
        "spss_twostep_cluster",
        dict(continuous=["engagement_total"], categorical=["gender", "major"]),
        "Cluster",
        survey,
    ),
    (
        "discriminant",
        "spss_discriminant",
        dict(groups="gender", predictors=["cognitive", "affective", "behavioral"]),
        "Canonical",
        survey,
    ),
    (
        "manova",
        "spss_manova",
        dict(dependents=["cognitive", "affective"], factors=["gender"]),
        "Multivariate",
        survey,
    ),
    (
        "ttest_independent",
        "spss_t_test",
        dict(
            test_type="independent", variables=["posttest"], grouping_variable="group"
        ),
        "Independent Samples Test",
        experiment,
    ),
    (
        "ttest_paired",
        "spss_t_test",
        dict(test_type="paired", variables=["pretest", "posttest"]),
        "Paired Samples Test",
        experiment,
    ),
    (
        "ttest_one_sample",
        "spss_t_test",
        dict(test_type="one_sample", variables=["gain"], test_value=0),
        "One-Sample",
        experiment,
    ),
    (
        "nonparam_mann_whitney",
        "spss_nonparametric_tests",
        dict(
            test_type="mann_whitney",
            variables=["posttest"],
            grouping_variable="group",
            group_values=[1, 2],
        ),
        "Mann-Whitney",
        experiment,
    ),
    (
        "nonparam_wilcoxon",
        "spss_nonparametric_tests",
        dict(test_type="wilcoxon", variables=["pretest", "posttest"]),
        "Wilcoxon",
        experiment,
    ),
    (
        "repeated_measures_anova",
        "spss_repeated_measures_anova",
        dict(within_factor_name="time", levels=2, variables=["pretest", "posttest"]),
        "Within-Subjects",
        experiment,
    ),
    (
        "kaplan_meier",
        "spss_kaplan_meier",
        dict(
            time_variable="time",
            status_variable="status",
            status_event_value=1,
            strata="treatment",
        ),
        "Kaplan-Meier",
        survival,
    ),
    (
        "cox_regression",
        "spss_cox_regression",
        dict(
            time_variable="time",
            status_variable="status",
            status_event_value=1,
            predictors=["treatment"],
        ),
        "Variables in the Equation",
        survival,
    ),
    (
        "logistic_regression",
        "spss_logistic_regression",
        dict(dependent="status", predictors=["treatment", "time"]),
        "Variables in the Equation",
        survival,
    ),
    (
        "regression",
        "spss_regression",
        dict(dependent="performance", predictors=["autonomy", "satisfaction"]),
        "Model Summary",
        mediation,
    ),
    (
        "ordinal_regression",
        "spss_ordinal_regression",
        dict(dependent="performance", predictors=["autonomy", "satisfaction"]),
        "Parameter Estimates",
        mediation,
    ),
    (
        "mixed",
        "spss_mixed",
        dict(
            dependent="score",
            fixed_effects=["time", "group"],
            subject="id",
            repeated="time",
        ),
        "Fixed Effects",
        long_data,
    ),
    (
        "genlinmixed",
        "spss_genlinmixed",
        dict(dependent="score", fixed_effects=["time", "group"], subject="id"),
        "Fixed Effects",
        long_data,
    ),
]


async def run_case(
    name: str, tool_name: str, kwargs: dict, marker: str, loader
) -> dict:
    fn = getattr(server, tool_name)
    started = time.perf_counter()
    try:
        output = await fn(file_path=loader("x"), **kwargs)
    except Exception as exc:  # pragma: no cover - depends on SPSS state
        return {
            "case": name,
            "tool": tool_name,
            "ok": False,
            "error": f"exception: {exc}",
            "marker_hit": False,
            "seconds": round(time.perf_counter() - started, 1),
        }
    elapsed = round(time.perf_counter() - started, 1)
    failed = output.strip().startswith("Error:")
    marker_hit = marker in output
    return {
        "case": name,
        "tool": tool_name,
        "ok": (not failed) and marker_hit,
        "error": None if not failed else output.strip().splitlines()[0][:160],
        "marker_hit": marker_hit,
        "seconds": elapsed,
    }


async def main() -> int:
    engine = get_engine()
    ok, msg = await engine.ensure_started()
    print(f"engine start: {ok} - {msg}")
    if not ok:
        return 1

    results = []
    for name, tool, kwargs, marker, loader in CASES:
        res = await run_case(name, tool, kwargs, marker, loader)
        results.append(res)
        status = "OK " if res["ok"] else "FAIL"
        print(
            f"[{status}] {res['case']:<24} {res['tool']:<26} "
            f"{res['seconds']:>5}s marker={res['marker_hit']} {res['error'] or ''}"
        )

    await engine.stop()
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    failed = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed -> {OUT}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
