"""P1 archive: export representative charts for the four sample datasets.

Loads each .sav under ``examples/data`` through the SPSS engine and exports a
set of representative publication-ready PNGs into ``examples/charts``.

Usage:
    python scripts/archive_sample_charts.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from spss_mcp.chart_service import export_chart
from spss_mcp.chart_spec import (
    BarErrorSpec,
    BarSpec,
    BoxplotSpec,
    ErrorbarSpec,
    HistogramDensitySpec,
    HistogramSpec,
    KMCurveSpec,
    ScatterSpec,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
DATA_DIR = EXAMPLES / "data"
CHARTS_DIR = EXAMPLES / "charts"

JOBS = [
    # (archive name, chart spec, data file)
    (
        "survey_engagement_histogram_density",
        HistogramDensitySpec(
            variable="engagement_total",
            title="学习投入总分分布（带正态密度）",
            x_label="学习投入总分",
            y_label="频数",
        ),
        "survey_study.sav",
    ),
    (
        "survey_engagement_by_major",
        BarErrorSpec(
            category="major",
            value="engagement_total",
            title="不同专业学习投入总分均值（95% CI）",
            x_label="专业",
            y_label="学习投入总分",
        ),
        "survey_study.sav",
    ),
    (
        "survey_engagement_by_gender",
        ErrorbarSpec(
            category="gender",
            value="engagement_total",
            title="不同性别学习投入总分均值（95% CI）",
            x_label="性别",
            y_label="学习投入总分",
        ),
        "survey_study.sav",
    ),
    (
        "experiment_posttest_boxplot",
        BoxplotSpec(
            variable="posttest",
            category="group",
            title="实验后测成绩箱线图（按组别）",
            x_label="组别",
            y_label="后测成绩",
        ),
        "experiment_study.sav",
    ),
    (
        "experiment_gain_errorbar",
        ErrorbarSpec(
            category="group",
            value="gain",
            title="前后测增益均值（95% CI）",
            x_label="组别",
            y_label="增益",
        ),
        "experiment_study.sav",
    ),
    (
        "experiment_posttest_bar",
        BarSpec(
            category="group",
            value="posttest",
            stat="mean",
            title="后测成绩均值（按组别）",
            x_label="组别",
            y_label="后测成绩",
        ),
        "experiment_study.sav",
    ),
    (
        "survival_km_curve",
        KMCurveSpec(
            time="time",
            status="status",
            event=1,
            group="treatment",
            title="Kaplan-Meier 生存曲线（按治疗方案）",
        ),
        "survival_study.sav",
    ),
    (
        "survival_time_histogram",
        HistogramSpec(
            variable="time",
            title="随访时间分布",
            x_label="随访月数",
            y_label="频数",
        ),
        "survival_study.sav",
    ),
    (
        "mediation_autonomy_performance_scatter",
        ScatterSpec(
            x="autonomy",
            y="performance",
            title="工作自主性与工作绩效散点图",
            x_label="工作自主性",
            y_label="工作绩效",
        ),
        "mediation_study.sav",
    ),
    (
        "mediation_satisfaction_performance_scatter",
        ScatterSpec(
            x="satisfaction",
            y="performance",
            title="工作满意度与工作绩效散点图",
            x_label="工作满意度",
            y_label="工作绩效",
        ),
        "mediation_study.sav",
    ),
    (
        "mediation_performance_histogram_density",
        HistogramDensitySpec(
            variable="performance",
            title="工作绩效分布（带正态密度）",
            x_label="工作绩效",
            y_label="频数",
        ),
        "mediation_study.sav",
    ),
]


async def main() -> int:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    failed = 0
    for name, spec, data_name in JOBS:
        data_file = str(DATA_DIR / data_name)
        result = await export_chart(spec, image_format="PNG", data_file=data_file)
        if not result["success"]:
            print(f"[FAIL] {name}: {result.get('error')}")
            failed += 1
            continue
        valid = [img for img in result["images"] if img["success"]]
        if not valid:
            print(f"[FAIL] {name}: no valid image produced")
            failed += 1
            continue
        src = Path(valid[0]["path"])
        dst = CHARTS_DIR / f"{name}.png"
        dst.write_bytes(src.read_bytes())
        print(
            f"[OK ] {name}: {dst.name} {valid[0]['width']}x{valid[0]['height']} "
            f"{valid[0]['bytes']} bytes @{valid[0]['dpi']}dpi"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
