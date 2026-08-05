"""Structured result parsing for SPSS text output (P2).

Turns the raw OMS TEXT output into JSON-friendly tables and a statistical
summary, and assembles the unified result payload ``{markdown, json, files,
warnings}`` shared by the MCP tools.

Summary rules cover the procedures most used in psychology/management
research: t-test, one-way ANOVA, correlations, linear regression, descriptive
statistics, frequencies, and Levene's homogeneity test.
"""

from __future__ import annotations

import re
from typing import Optional

# Matches integers (120), decimals (.000, 27.37, -3.875) and mixtures.
_NUMBER_RE = re.compile(r"-?\d*\.?\d+")
_FOOTNOTE_RE = re.compile(r"^[a-z] .*", re.IGNORECASE)
_BOILERPLATE_KW = (
    "IBM SPSS Statistics",
    "Licensed Materials",
    "SPSS for Windows",
    "Copyright IBM",
)


def _split_fixed_row(line: str) -> list[str]:
    """Split a fixed-width SPSS row by whitespace (2+ spaces) or pipe chars."""
    parts = re.split(r"\s{2,}|\|", line)
    return [p.strip() for p in parts if p.strip()]


def _is_separator_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    non_dash = re.sub(r"[-\s|+]", "", stripped)
    return len(non_dash) == 0 and len(stripped) >= 3


def _cells_to_number(cell: str) -> Optional[float]:
    """Best-effort float conversion, stripping footnote markers like (a)."""
    cleaned = re.sub(r"[()a-z*]+", "", cell, flags=re.IGNORECASE).strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _nums(text: str) -> list[float]:
    """All numeric literals in a text (e.g. .000, -3.875, 120, 1695.246)."""
    return [float(m) for m in _NUMBER_RE.findall(text)]


def _p_format(value: float) -> str:
    """Format a p-value literal like SPSS prints it (.000 -> '<.001')."""
    if value < 0.001:
        return "<.001"
    return f"{value:.3f}".lstrip("0") or ".0"


def _sig_of(text: str) -> Optional[str]:
    """Return the last p-value-like literal (< 1) found in a text."""
    matches = _NUMBER_RE.findall(text)
    for raw in reversed(matches):
        try:
            value = float(raw)
        except ValueError:
            continue
        if 0.0 <= value < 1.0:
            return _p_format(value)
    return None


def _label_of(text: str) -> str:
    """Strip numeric literals and footnotes to recover a row label."""
    cleaned = _NUMBER_RE.sub(" ", text)
    cleaned = re.sub(r"\([a-z]+\)", " ", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("*", " ")
    cleaned = re.sub(r"\(\s*\)", " ", cleaned)
    return " ".join(cleaned.split())


# --------------------------------------------------------------------------
# Table extraction (line-scan state machine)
#
# SPSS text output layout:
#   <command title>            (e.g. "Oneway", directly above "Notes")
#   Notes                     (log block to skip)
#   <notes lines, no blanks>
#   (blank)
#   <table title>             (standalone short line)
#   <subtitle>                (optional, e.g. variable name)
#   (blank)
#   <header lines>
#   <data lines>
#   <footnote lines>
#   (blank)
# --------------------------------------------------------------------------


def parse_tables(raw_text: str) -> list[dict]:
    """Parse raw SPSS text output into structured table dicts.

    Each table: ``{"title": str, "headers": [str], "rows": [[str]]}``.  The
    parser is lenient: SPSS multi-line headers are folded to the first header
    row and cell alignment is best-effort.
    """
    if not raw_text or not raw_text.strip():
        return []

    tables: list[dict] = []
    current: Optional[dict] = None
    prev_blank = True
    skip = False

    def flush() -> None:
        nonlocal current
        if current is not None and current["rows"]:
            tables.append(current)
        current = None

    for line in raw_text.splitlines():
        if any(kw in line for kw in _BOILERPLATE_KW):
            prev_blank = False
            continue
        stripped = line.strip()
        if not stripped:
            prev_blank = True
            continue

        cells = _split_fixed_row(line)
        single_cell = len(cells) == 1

        if stripped == "Notes":
            flush()
            current = None
            skip = True
            prev_blank = False
            continue

        title_candidate = (
            prev_blank
            and single_cell
            and not line.startswith((" ", "\t"))
            and not _FOOTNOTE_RE.match(stripped)
        )
        prev_blank = False

        if skip:
            if title_candidate:
                skip = False
                current = {"title": stripped, "headers": [], "rows": []}
            continue

        if title_candidate:
            flush()
            current = {"title": stripped, "headers": [], "rows": []}
            continue

        if current is None:
            continue

        if _is_separator_line(line):
            continue

        if (
            single_cell
            and not current["rows"]
            and not current.get("_subtitle_used")
            and not _nums(stripped)
        ):
            current["title"] = f"{current['title']} ({stripped})"
            current["_subtitle_used"] = True
            continue

        current["rows"].append(cells)

    flush()
    return _finalize_tables(tables)


def _finalize_tables(tables: list[dict]) -> list[dict]:
    """Fold headers and drop degenerate blocks."""
    cleaned = []
    for table in tables:
        rows = table["rows"]
        if not rows:
            continue
        if not re.search(r"\.\d", " ".join(rows[0])):
            headers = rows[0]
            body = rows[1:]
        else:
            headers = []
            body = rows
        max_cols = max([len(headers)] + [len(r) for r in body])
        headers = headers + [""] * (max_cols - len(headers))
        body = [r + [""] * (max_cols - len(r)) for r in body]
        if not any(_nums(" ".join(row)) for row in body):
            continue
        cleaned.append({"title": table["title"], "headers": headers, "rows": body})
    return cleaned


# --------------------------------------------------------------------------
# Statistical summary
# --------------------------------------------------------------------------


def _summarize_descriptive_statistics(table: dict) -> dict:
    stats = []
    for row in table["rows"]:
        text = " ".join(row)
        nums = _nums(text)
        if len(nums) < 5:
            continue
        label = _label_of(text)
        if not label or label.lower().startswith("valid n"):
            continue
        stats.append(
            {
                "variable": label,
                "n": nums[0],
                "min": nums[1],
                "max": nums[2],
                "mean": nums[3],
                "std": nums[4],
            }
        )
    return {"tables": ["Descriptive Statistics"], "statistics": stats}


def _summarize_model_summary(table: dict) -> dict:
    header_text = " ".join(table["headers"]).lower()
    for row in table["rows"]:
        nums = _nums(" ".join(row))
        if len(nums) < 4:
            continue
        if "log likelihood" in header_text:
            return {
                "tables": ["Model Summary (logistic)"],
                "statistics": {
                    "-2_log_likelihood": nums[1],
                    "cox_snell_r_square": nums[2],
                    "nagelkerke_r_square": nums[3],
                },
            }
        return {
            "tables": ["Model Summary"],
            "statistics": {
                "r": nums[1],
                "r_square": nums[2],
                "adjusted_r_square": nums[3],
            },
        }
    return {"tables": ["Model Summary"], "statistics": {}}


def _summarize_anova(table: dict) -> dict:
    stats = {"f": None, "df1": None, "df2": None, "p": None}
    for row in table["rows"]:
        text = " ".join(row)
        nums = _nums(text)
        label = _label_of(text).lower()
        if "regression" in label or "between groups" in label:
            if len(nums) >= 5:
                stats["f"] = nums[-2]
                stats["p"] = _sig_of(text)
                stats["df1"] = nums[1] if len(nums) == 5 else nums[2]
        elif "within groups" in label or "residual" in label:
            if len(nums) >= 3:
                stats["df2"] = nums[1] if len(nums) == 3 else nums[2]
    if stats["f"] is None:
        return {"tables": ["ANOVA"], "statistics": {}}
    return {"tables": ["ANOVA"], "statistics": stats}


def _summarize_coefficients(table: dict) -> dict:
    terms = []
    for row in table["rows"]:
        text = " ".join(row)
        nums = _nums(text)
        label = _label_of(text)
        if "(constant)" in text.lower():
            # Leading Model column is an integer when present.
            offset = 1 if nums and float(nums[0]).is_integer() else 0
            if len(nums) < offset + 5:
                continue
            p = _p_format(nums[offset + 3]) if nums[offset + 3] < 1 else None
            terms.append(
                {
                    "term": "Constant",
                    "b": nums[offset],
                    "std_error": nums[offset + 1],
                    "t": nums[offset + 2],
                    "p": p,
                }
            )
        else:
            if len(nums) < 5 or not label or label.lower() == "model":
                continue
            p = _p_format(nums[4]) if nums[4] < 1 else None
            terms.append(
                {
                    "term": label,
                    "b": nums[0],
                    "std_error": nums[1],
                    "beta": nums[2],
                    "t": nums[3],
                    "p": p,
                }
            )
    if not terms:
        return {"tables": ["Coefficients"], "statistics": {}}
    return {"tables": ["Coefficients"], "statistics": {"terms": terms}}


def _summarize_correlations(table: dict) -> dict:
    pearson_rows = []
    sig_rows = []
    for row in table["rows"]:
        text = " ".join(row)
        lower = text.lower()
        if "pearson correlation" in lower:
            nums = _nums(text)
            non_diag = [n for n in nums if abs(n - 1.0) > 1e-6]
            if non_diag:
                var = _label_of(text).replace("Pearson Correlation", "").strip()
                pearson_rows.append((var, non_diag[-1]))
        elif lower.startswith("sig"):
            sig = _sig_of(text)
            if sig:
                sig_rows.append(sig)
    pairs = []
    for i, (var, r) in enumerate(pearson_rows):
        if i == 0:
            continue  # first variable's row is the diagonal for itself
        with_var = pearson_rows[0][0]
        pairs.append(
            {
                "variable": var,
                "with": with_var,
                "r": r,
                "p": sig_rows[i] if i < len(sig_rows) else None,
            }
        )
    if not pairs:
        return {"tables": ["Correlations"], "statistics": {}}
    return {"tables": ["Correlations"], "statistics": {"pairs": pairs}}


def _summarize_ttest(table: dict) -> dict:
    for row in table["rows"]:
        text = " ".join(row)
        nums = _nums(text)
        if len(nums) < 6:
            continue
        label = _label_of(text).lower()
        if "equal" not in label:
            continue
        p = _p_format(nums[3]) if nums[3] < 1 else None
        return {
            "tables": ["Independent Samples Test"],
            "statistics": {
                "t": nums[0],
                "df": nums[1],
                "p": p,
                "mean_difference": nums[4],
            },
        }
    return {"tables": ["Independent Samples Test"], "statistics": {}}


def _summarize_group_statistics(table: dict) -> dict:
    groups = []
    for row in table["rows"]:
        text = " ".join(row)
        nums = _nums(text)
        if len(nums) < 4:
            continue
        group_value = _NUMBER_RE.findall(text)[0]
        groups.append(
            {"group": group_value, "n": nums[1], "mean": nums[2], "std": nums[3]}
        )
    if not groups:
        return {"tables": ["Group Statistics"], "statistics": {}}
    return {"tables": ["Group Statistics"], "statistics": {"groups": groups}}


def _summarize_frequencies(table: dict) -> dict:
    stats = {}
    candidates = [table["headers"]] + list(table["rows"])
    for row in candidates:
        text = " ".join(row)
        label = _label_of(text).lower()
        nums = _nums(text)
        if not nums:
            continue
        if label.startswith("n valid"):
            stats["n"] = nums[0]
        elif label == "mean":
            stats["mean"] = nums[0]
        elif label == "median":
            stats["median"] = nums[0]
        elif label.startswith("mode"):
            stats["mode"] = nums[0]
        elif label.startswith("std"):
            stats["std"] = nums[0]
    if not stats:
        return {"tables": ["Statistics"], "statistics": {}}
    return {"tables": ["Statistics"], "statistics": stats}


def _summarize_levene(table: dict) -> dict:
    for row in table["rows"]:
        text = " ".join(row)
        nums = _nums(text)
        if len(nums) >= 4 and "based on" in text.lower():
            return {
                "tables": ["Tests of Homogeneity of Variances"],
                "statistics": {
                    "levene_f": nums[0],
                    "df1": nums[1],
                    "df2": nums[2],
                    "p": _sig_of(text),
                },
            }
        if len(nums) >= 2 and "levene" in table["title"].lower():
            return {
                "tables": ["Levene's Test for Equality of Variances"],
                "statistics": {"levene_f": nums[0], "p": _sig_of(text)},
            }
    return {"tables": ["Tests of Homogeneity of Variances"], "statistics": {}}


def _summarize_paired_ttest(table: dict) -> dict:
    for row in table["rows"]:
        text = re.sub(r"Pair\s+\d+", "", " ".join(row))
        nums = _nums(text)
        if len(nums) < 8:
            continue
        p = _p_format(nums[-1]) if nums[-1] < 1 else None
        return {
            "tables": ["Paired Samples Test"],
            "statistics": {
                "t": nums[5],
                "df": nums[6],
                "p": p,
                "mean_difference": nums[0],
            },
        }
    return {"tables": ["Paired Samples Test"], "statistics": {}}


def _summarize_chi_square(table: dict) -> dict:
    for row in table["rows"]:
        text = " ".join(row)
        label = _label_of(text).lower()
        if "pearson" not in label:
            continue
        nums = _nums(text)
        if len(nums) >= 3:
            p = _p_format(nums[2]) if nums[2] < 1 else None
            return {
                "tables": ["Chi-Square Tests"],
                "statistics": {"chi_square": nums[0], "df": nums[1], "p": p},
            }
    return {"tables": ["Chi-Square Tests"], "statistics": {}}


def _summarize_reliability(table: dict) -> dict:
    for row in table["rows"]:
        nums = _nums(" ".join(row))
        if len(nums) >= 2 and abs(nums[0]) <= 1.0:
            return {
                "tables": ["Reliability Statistics"],
                "statistics": {"cronbach_alpha": nums[0], "n_items": nums[1]},
            }
    return {"tables": ["Reliability Statistics"], "statistics": {}}


def _summarize_between_subjects(table: dict) -> dict:
    terms = []
    df2 = None
    skip = {"corrected model", "intercept", "total", "corrected total", "error"}
    for row in table["rows"]:
        text = " ".join(row)
        nums = _nums(text)
        label = _label_of(text)
        if not label:
            continue
        low = label.lower()
        if low == "error" and len(nums) >= 3:
            df2 = nums[1]
            continue
        if low in skip or len(nums) < 6:
            continue
        p = _p_format(nums[4]) if nums[4] < 1 else None
        terms.append(
            {
                "term": label,
                "f": nums[3],
                "df1": nums[1],
                "p": p,
                "partial_eta_squared": nums[5],
            }
        )
    if not terms:
        return {"tables": ["Tests of Between-Subjects Effects"], "statistics": {}}
    return {
        "tables": ["Tests of Between-Subjects Effects"],
        "statistics": {"terms": terms, "df2": df2},
    }


def _summarize_normality(table: dict) -> dict:
    for row in table["rows"]:
        nums = _nums(" ".join(row))
        if len(nums) >= 6:
            return {
                "tables": ["Tests of Normality"],
                "statistics": {
                    "shapiro_wilk_w": nums[3],
                    "shapiro_wilk_df": nums[4],
                    "shapiro_wilk_p": _p_format(nums[5]) if nums[5] < 1 else None,
                    "kolmogorov_smirnov_d": nums[0],
                    "kolmogorov_smirnov_df": nums[1],
                    "kolmogorov_smirnov_p": _p_format(nums[2]) if nums[2] < 1 else None,
                },
            }
    return {"tables": ["Tests of Normality"], "statistics": {}}


def _summarize_test_statistics(table: dict) -> dict:
    stats = {}
    for row in table["rows"]:
        text = " ".join(row)
        label = _label_of(text).lower()
        nums = _nums(text)
        if not nums:
            continue
        if "mann-whitney u" in label:
            stats["u"] = nums[0]
        elif "wilcoxon w" in label:
            stats["wilcoxon_w"] = nums[0]
        elif "kruskal-wallis h" in label:
            stats["h"] = nums[0]
        elif label == "z":
            stats["z"] = nums[0]
        elif label == "df":
            stats["df"] = nums[0]
        elif label.startswith("asymp. sig"):
            stats["p"] = _sig_of(text)
    if not stats:
        return {"tables": ["Test Statistics"], "statistics": {}}
    return {"tables": ["Test Statistics"], "statistics": stats}


def _summarize_kmo(table: dict) -> dict:
    stats = {}
    for row in table["rows"]:
        text = " ".join(row)
        label = _label_of(text).lower()
        nums = _nums(text)
        if not nums:
            continue
        if "kaiser-meyer" in label:
            stats["kmo"] = nums[0]
        elif "chi-square" in label:
            stats["bartlett_chi_square"] = nums[0]
        elif label == "df":
            stats["bartlett_df"] = nums[0]
        elif label.startswith("sig"):
            stats["bartlett_p"] = _p_format(nums[0]) if nums[0] < 1 else None
    if not stats:
        return {"tables": ["KMO and Bartlett's Test"], "statistics": {}}
    return {"tables": ["KMO and Bartlett's Test"], "statistics": stats}


def _summarize_total_variance(table: dict) -> dict:
    components = []
    for row in table["rows"]:
        nums = _nums(" ".join(row))
        if len(nums) < 4:
            continue
        components.append(
            {
                "component": nums[0],
                "eigenvalue": nums[1],
                "percent_variance": nums[2],
                "cumulative_percent": nums[3],
            }
        )
    if not components:
        return {"tables": ["Total Variance Explained"], "statistics": {}}
    over_one = [comp for comp in components if comp["eigenvalue"] > 1]
    return {
        "tables": ["Total Variance Explained"],
        "statistics": {
            "components": components[:3],
            "eigenvalue_over_1": len(over_one),
            "cumulative_percent": (
                over_one[-1]["cumulative_percent"]
                if over_one
                else components[-1]["cumulative_percent"]
            ),
        },
    }


def _summarize_logistic_variables(table: dict) -> dict:
    terms = []
    for row in table["rows"]:
        text = " ".join(row)
        if "step 0" in text.lower():
            continue
        nums = _nums(text)
        if len(nums) < 6:
            continue
        label = _label_of(text)
        if not label:
            continue
        offset = 1 if nums and float(nums[0]).is_integer() else 0
        p = _p_format(nums[offset + 4]) if nums[offset + 4] < 1 else None
        terms.append(
            {
                "term": label,
                "b": nums[offset],
                "std_error": nums[offset + 1],
                "wald": nums[offset + 2],
                "df": nums[offset + 3],
                "p": p,
                "exp_b": nums[offset + 5],
            }
        )
    if not terms:
        return {"tables": ["Variables in the Equation"], "statistics": {}}
    return {"tables": ["Variables in the Equation"], "statistics": {"terms": terms}}


def _summarize_omnibus(table: dict) -> dict:
    for row in table["rows"]:
        text = " ".join(row)
        label = _label_of(text).lower()
        if not label.startswith("model"):
            continue
        nums = _nums(text)
        if len(nums) >= 3:
            p = _p_format(nums[2]) if nums[2] < 1 else None
            return {
                "tables": ["Omnibus Tests of Model Coefficients"],
                "statistics": {"chi_square": nums[0], "df": nums[1], "p": p},
            }
    return {"tables": ["Omnibus Tests of Model Coefficients"], "statistics": {}}


_SUMMARIZERS = {
    "Descriptive Statistics": _summarize_descriptive_statistics,
    "Model Summary": _summarize_model_summary,
    "ANOVA": _summarize_anova,
    "ANOVA(a)": _summarize_anova,
    "Coefficients": _summarize_coefficients,
    "Coefficients(a)": _summarize_coefficients,
    "Correlations": _summarize_correlations,
    "Independent Samples Test": _summarize_ttest,
    "Group Statistics": _summarize_group_statistics,
    "Statistics": _summarize_frequencies,
    "Tests of Homogeneity of Variances": _summarize_levene,
    "Levene's Test for Equality of Variances": _summarize_levene,
    "Paired Samples Test": _summarize_paired_ttest,
    "Chi-Square Tests": _summarize_chi_square,
    "Reliability Statistics": _summarize_reliability,
    "Tests of Between-Subjects Effects": _summarize_between_subjects,
    "Tests of Normality": _summarize_normality,
    "Test Statistics": _summarize_test_statistics,
    "Test Statistics(a)": _summarize_test_statistics,
    "Test Statistics(a,b)": _summarize_test_statistics,
    "KMO and Bartlett's Test": _summarize_kmo,
    "Total Variance Explained": _summarize_total_variance,
    "Variables in the Equation": _summarize_logistic_variables,
    "Omnibus Tests of Model Coefficients": _summarize_omnibus,
}


def summarize_analysis(raw_text: str, tables: Optional[list[dict]] = None) -> dict:
    """Return a statistical summary extracted from raw SPSS text output."""
    if tables is None:
        tables = parse_tables(raw_text)
    summaries = []
    for table in tables:
        base_title = table["title"].split(" (")[0]
        summarizer = _SUMMARIZERS.get(table["title"]) or _SUMMARIZERS.get(base_title)
        if summarizer:
            summary = summarizer(table)
            if summary["statistics"]:
                summaries.append(summary)
    return {"summaries": summaries, "text": _build_summary_text(summaries)}


def _build_summary_text(summaries: list[dict]) -> str:
    lines = []
    for s in summaries:
        stats = s["statistics"]
        if "f" in stats and stats.get("df1") is not None and stats.get("p"):
            df2 = int(stats["df2"]) if stats.get("df2") is not None else 0
            lines.append(
                f"ANOVA: F({int(stats['df1'])}, {df2}) = {stats['f']:.3f}, "
                f"p {stats['p']}."
            )
        if "t" in stats and stats.get("df") is not None and stats.get("p"):
            label = (
                "Paired t-test"
                if s["tables"][0] == "Paired Samples Test"
                else "Independent-samples t-test"
            )
            lines.append(
                f"{label}: t({int(stats['df'])}) = {stats['t']:.3f}, "
                f"p {stats['p']}, mean difference = {stats.get('mean_difference', 0):.3f}."
            )
        if "r" in stats and "r_square" in stats:
            lines.append(
                f"Regression model: R = {stats['r']:.3f}, "
                f"R square = {stats['r_square']:.3f}."
            )
        if "terms" in stats:
            for term in stats["terms"]:
                if "b" in term:
                    parts = [f"{term['term']}: B = {term['b']:.3f}"]
                    if "beta" in term:
                        parts.append(f"Beta = {term['beta']:.3f}")
                elif "f" in term and term.get("df1") is not None:
                    parts = [
                        f"{term['term']}: F({int(term['df1'])}, "
                        f"{int(stats.get('df2') or 0)}) = {term['f']:.3f}"
                    ]
                    if term.get("partial_eta_squared") is not None:
                        parts.append(f"eta2 = {term['partial_eta_squared']:.3f}")
                else:
                    parts = [term["term"]]
                if term.get("p"):
                    parts.append(f"p {term['p']}")
                lines.append("Coefficient " + ", ".join(parts) + ".")
        if "pairs" in stats:
            for pair in stats["pairs"]:
                parts = [
                    f"Correlation {pair['variable']}-{pair['with']}: "
                    f"r = {pair['r']:.3f}"
                ]
                if pair.get("p"):
                    parts.append(f"p {pair['p']}")
                lines.append(", ".join(parts) + ".")
        if "z" in stats and stats.get("p"):
            lines.append(f"Wilcoxon/Mann-Whitney z = {stats['z']:.3f}, p {stats['p']}.")
        if "u" in stats:
            lines.append(f"Mann-Whitney U = {stats['u']:.3f}.")
        if "h" in stats and stats.get("p"):
            df = int(stats["df"]) if stats.get("df") is not None else 0
            lines.append(f"Kruskal-Wallis H({df}) = {stats['h']:.3f}, p {stats['p']}.")
        if "chi_square" in stats and stats.get("p"):
            df = int(stats["df"]) if stats.get("df") is not None else 0
            lines.append(
                f"Chi-square({df}) = {stats['chi_square']:.3f}, p {stats['p']}."
            )
        if "cronbach_alpha" in stats:
            lines.append(
                f"Cronbach's alpha = {stats['cronbach_alpha']:.3f} "
                f"({int(stats['n_items'])} items)."
            )
        if "shapiro_wilk_w" in stats:
            lines.append(
                f"Shapiro-Wilk W({int(stats['shapiro_wilk_df'])}) = "
                f"{stats['shapiro_wilk_w']:.3f}, p {stats['shapiro_wilk_p']}."
            )
        if "kmo" in stats:
            parts = [f"KMO = {stats['kmo']:.3f}"]
            if stats.get("bartlett_chi_square") is not None:
                df = (
                    int(stats["bartlett_df"])
                    if stats.get("bartlett_df") is not None
                    else 0
                )
                parts.append(
                    f"Bartlett's chi-square({df}) = {stats['bartlett_chi_square']:.3f}"
                )
            if stats.get("bartlett_p"):
                parts.append(f"p {stats['bartlett_p']}")
            lines.append(", ".join(parts) + ".")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Unified result payload
# --------------------------------------------------------------------------


def build_result_payload(result: dict) -> dict:
    """Assemble the unified ``{markdown, json, files, warnings}`` payload."""
    raw = result.get("output_raw") or ""
    tables = parse_tables(raw)
    summary = summarize_analysis(raw, tables)
    files = list(result.get("files") or [])
    for key in ("viewer_output_file", "syntax_file"):
        value = result.get(key)
        if value and value not in files:
            files.append(value)
    return {
        "markdown": result.get("output_markdown") or "_No output produced._",
        "json": {"tables": tables, "summary": summary},
        "files": files,
        "warnings": list(result.get("warnings") or []),
    }
