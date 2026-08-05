from pathlib import Path

import pytest

from spss_mcp.result_parser import (
    build_result_payload,
    parse_tables,
    summarize_analysis,
)

FIXTURES = Path(__file__).parent / "fixtures" / "spss_outputs"


def _load(name: str) -> str:
    return (FIXTURES / f"{name}.txt").read_text(encoding="utf-8")


def test_parse_tables_skips_notes_block():
    tables = parse_tables(_load("descriptives"))
    assert all("notes" not in t["title"].lower() for t in tables)
    assert any(t["title"].startswith("Descriptive Statistics") for t in tables)


def test_parse_tables_detects_titles_and_rows():
    tables = parse_tables(_load("anova"))
    anova = next(t for t in tables if t["title"].startswith("ANOVA"))
    assert any("Between Groups" in " ".join(row) for row in anova["rows"])


def test_summarize_descriptives():
    summary = summarize_analysis(_load("descriptives"))
    stats = summary["summaries"][0]["statistics"]
    score = next(s for s in stats if s["variable"] == "score")
    assert score["n"] == 120
    assert score["mean"] == pytest.approx(54.1966)


def test_summarize_anova():
    summary = summarize_analysis(_load("anova"))
    by_table = {s["tables"][0]: s["statistics"] for s in summary["summaries"]}
    anova = by_table["ANOVA"]
    assert anova["f"] == pytest.approx(15.012)
    assert anova["df1"] == 1
    assert anova["df2"] == 118
    assert anova["p"] == "<.001"


def test_summarize_correlations():
    summary = summarize_analysis(_load("corr"))
    pairs = summary["summaries"][0]["statistics"]["pairs"]
    assert pairs[0]["variable"] == "y"
    assert pairs[0]["with"] == "x"
    assert pairs[0]["r"] == pytest.approx(0.419)
    assert pairs[0]["p"] == "<.001"


def test_summarize_regression():
    summary = summarize_analysis(_load("regression"))
    by_table = {s["tables"][0]: s["statistics"] for s in summary["summaries"]}
    model = by_table["Model Summary"]
    assert model["r"] == pytest.approx(0.824)
    assert model["r_square"] == pytest.approx(0.680)
    anova = by_table["ANOVA"]
    assert anova["f"] == pytest.approx(124.029)
    terms = by_table["Coefficients"]["terms"]
    x = next(t for t in terms if t["term"] == "x")
    assert x["b"] == pytest.approx(0.923)
    assert x["beta"] == pytest.approx(0.476)
    assert x["p"] == "<.001"


def test_summarize_ttest():
    summary = summarize_analysis(_load("ttest"))
    by_table = {s["tables"][0]: s["statistics"] for s in summary["summaries"]}
    test = by_table["Independent Samples Test"]
    assert test["t"] == pytest.approx(-3.875)
    assert test["df"] == 118
    assert test["p"] == "<.001"
    groups = by_table["Group Statistics"]["groups"]
    assert len(groups) == 2
    assert groups[0]["group"] == ".00"
    assert groups[0]["n"] == 60


def test_summarize_frequencies():
    summary = summarize_analysis(_load("frequencies"))
    stats = summary["summaries"][0]["statistics"]
    assert stats["n"] == 120
    assert stats["mean"] == pytest.approx(0.5)
    assert stats["std"] == pytest.approx(0.5021)


def test_summary_text_mentions_anova():
    summary = summarize_analysis(_load("anova"))
    assert "ANOVA: F(1, 118) = 15.012" in summary["text"]


def test_parse_tables_empty_input():
    assert parse_tables("") == []
    assert parse_tables(None) == []


def test_build_result_payload_unified_structure():
    result = {
        "output_raw": _load("ttest"),
        "output_markdown": "# T-Test",
        "warnings": ["w1"],
        "viewer_output_file": "C:/out.spv",
        "syntax_file": "C:/out.sps",
    }
    payload = build_result_payload(result)
    assert set(payload) == {"markdown", "json", "files", "warnings"}
    assert payload["markdown"] == "# T-Test"
    assert payload["warnings"] == ["w1"]
    assert "C:/out.spv" in payload["files"]
    assert payload["json"]["summary"]["summaries"]
    assert payload["json"]["tables"]


def test_parse_tables_handles_none():
    assert parse_tables(None) == []


# --- additional analysis types ---


def _summary_by_table(raw_text: str) -> dict:
    summary = summarize_analysis(raw_text)
    return {s["tables"][0]: s["statistics"] for s in summary["summaries"]}


def test_summarize_paired_ttest():
    stats = _summary_by_table(_load("paired_ttest"))["Paired Samples Test"]
    assert stats["t"] == pytest.approx(-12.836)
    assert stats["df"] == 119
    assert stats["p"] == "<.001"
    assert stats["mean_difference"] == pytest.approx(-9.8833)


def test_summarize_chi_square():
    stats = _summary_by_table(_load("crosstabs_chisq"))["Chi-Square Tests"]
    assert stats["chi_square"] == pytest.approx(0.605)
    assert stats["df"] == 2
    assert stats["p"] == ".739"


def test_summarize_reliability():
    stats = _summary_by_table(_load("reliability"))["Reliability Statistics"]
    assert stats["cronbach_alpha"] == pytest.approx(-0.156)
    assert stats["n_items"] == 4


def test_summarize_between_subjects_effects():
    stats = _summary_by_table(_load("unianova"))["Tests of Between-Subjects Effects"]
    assert stats["df2"] == 194
    gender = next(t for t in stats["terms"] if t["term"] == "gender")
    assert gender["f"] == pytest.approx(0.342)
    assert gender["p"] == ".559"
    assert gender["partial_eta_squared"] == pytest.approx(0.002)


def test_summarize_normality():
    stats = _summary_by_table(_load("normality"))["Tests of Normality"]
    assert stats["shapiro_wilk_w"] == pytest.approx(0.988)
    assert stats["shapiro_wilk_p"] == ".101"
    assert stats["kolmogorov_smirnov_d"] == pytest.approx(0.073)


def test_summarize_mann_whitney():
    stats = _summary_by_table(_load("mann_whitney"))["Test Statistics"]
    assert stats["u"] == pytest.approx(1088.5)
    assert stats["z"] == pytest.approx(-3.717)
    assert stats["p"] == "<.001"


def test_summarize_wilcoxon():
    stats = _summary_by_table(_load("wilcoxon"))["Test Statistics"]
    assert stats["z"] == pytest.approx(-8.614)
    assert stats["p"] == "<.001"


def test_summarize_kruskal_wallis():
    stats = _summary_by_table(_load("kruskal_wallis"))["Test Statistics"]
    assert stats["h"] == pytest.approx(0.775)
    assert stats["df"] == 2
    assert stats["p"] == ".679"


def test_summarize_factor():
    stats = _summary_by_table(_load("factor"))
    kmo = stats["KMO and Bartlett's Test"]
    assert kmo["kmo"] == pytest.approx(0.504)
    assert kmo["bartlett_chi_square"] == pytest.approx(64.684)
    variance = stats["Total Variance Explained"]
    assert variance["eigenvalue_over_1"] == 6
    assert variance["cumulative_percent"] == pytest.approx(59.825)


def test_summarize_logistic_regression():
    stats = _summary_by_table(_load("logistic_regression"))
    model = stats["Model Summary (logistic)"]
    assert model["-2_log_likelihood"] == pytest.approx(147.124)
    assert model["cox_snell_r_square"] == pytest.approx(0.001)
    terms = stats["Variables in the Equation"]["terms"]
    constant = next(t for t in terms if t["term"] == "Constant")
    assert constant["b"] == pytest.approx(1.065)
    assert constant["exp_b"] == pytest.approx(2.902)
    treatment = next(t for t in terms if "方案" in t["term"])
    assert treatment["b"] == pytest.approx(0.187)
    assert treatment["wald"] == pytest.approx(0.163)


def test_summary_text_new_types():
    assert "Shapiro-Wilk" in summarize_analysis(_load("normality"))["text"]
    assert "Kruskal-Wallis" in summarize_analysis(_load("kruskal_wallis"))["text"]
    assert "Cronbach" in summarize_analysis(_load("reliability"))["text"]
    assert "Paired t-test" in summarize_analysis(_load("paired_ttest"))["text"]
