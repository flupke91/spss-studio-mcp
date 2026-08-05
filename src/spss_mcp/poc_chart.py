"""P1 PoC runner: GGRAPH -> OMS IMAGE -> PNG end-to-end on a real SPSS.

Usage:
    python -m spss_mcp.poc_chart [--format PNG|TIFF|EMF] [--width 1950] [--height 1500]

Generates a 200-case in-memory dataset, exports four paper-ready charts
(histogram / scatter / bar / line) and validates every image with Pillow.
Exit code is 0 only when all charts are produced and validated.
"""

from __future__ import annotations

import argparse
import sys

from spss_mcp.chart_service import export_chart
from spss_mcp.chart_spec import (
    AreaSpec,
    BarErrorSpec,
    BarSpec,
    BoxplotSpec,
    ErrorbarSpec,
    HistogramDensitySpec,
    HistogramSpec,
    KMCurveSpec,
    LineSpec,
    QQPlotSpec,
    ScatterSpec,
)

SAMPLE_DATA_SYNTAX = """INPUT PROGRAM.
LOOP #i = 1 TO 200.
  COMPUTE group = MOD(#i, 3).
  COMPUTE score = RV.NORMAL(50, 10).
  COMPUTE x = RV.UNIFORM(0, 100).
  COMPUTE y = 2 * x + RV.NORMAL(0, 15).
  COMPUTE time = RV.EXP(2) + 1.
  COMPUTE status = RV.BERNOULLI(0.7).
  END CASE.
END LOOP.
END FILE.
END INPUT PROGRAM.
EXECUTE.
DESCRIPTIVES VARIABLES=score x y time.
"""


def _specs() -> list:
    return [
        HistogramSpec(
            variable="score",
            title="Histogram of score",
            x_label="Score",
            y_label="Frequency",
        ),
        ScatterSpec(
            x="x",
            y="y",
            title="Scatter of y vs x",
            x_label="x",
            y_label="y",
        ),
        BarSpec(
            category="group",
            value="score",
            stat="mean",
            title="Mean score by group",
            x_label="Group",
            y_label="Mean score",
        ),
        LineSpec(
            x="x",
            y="y",
            title="Line of y vs x",
            x_label="x",
            y_label="y",
        ),
        BoxplotSpec(
            variable="score",
            category="group",
            title="Boxplot of score by group",
            x_label="Group",
            y_label="Score",
        ),
        ErrorbarSpec(
            category="group",
            value="score",
            title="Mean score with 95% CI by group",
            x_label="Group",
            y_label="Mean score",
        ),
        QQPlotSpec(variable="score", title="Normal Q-Q of score"),
        KMCurveSpec(
            time="time",
            status="status",
            group="group",
            title="Kaplan-Meier survival by group",
        ),
        AreaSpec(
            x="x",
            y="y",
            title="Area of y vs x",
            x_label="x",
            y_label="y",
        ),
        HistogramDensitySpec(
            variable="score",
            title="Histogram with normal density of score",
            x_label="Score",
            y_label="Frequency",
        ),
        BarErrorSpec(
            category="group",
            value="score",
            title="Mean score with 95% CI bars by group",
            x_label="Group",
            y_label="Mean score",
        ),
    ]


async def _run(image_format: str, width: int, height: int) -> int:
    from spss_mcp.spss_runner import run_syntax

    data_result = await run_syntax(SAMPLE_DATA_SYNTAX)
    if not data_result.get("success"):
        print(f"[FAIL] sample dataset generation: {data_result.get('error')}")
        print("Is SPSS licensed? Run `spss-studio-mcp status` to check.")
        return 1

    failed = False
    for spec in _specs():
        result = await export_chart(
            spec,
            image_format=image_format,
            width_px=width,
            height_px=height,
        )
        if result["success"]:
            for img in result["images"]:
                status = "OK " if img["success"] else "BAD"
                print(
                    f"[{status}] {spec.kind:<10} {img.get('path', '')} "
                    f"{img.get('width', 0)}x{img.get('height', 0)} "
                    f"{img.get('bytes', 0)} bytes {img.get('format', '')}"
                )
                if not img["success"]:
                    failed = True
        else:
            print(f"[FAIL] {spec.kind:<10} {result.get('error')}")
            failed = True

    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", default="PNG", choices=["PNG", "TIFF", "EMF"])
    parser.add_argument("--width", type=int, default=1950)
    parser.add_argument("--height", type=int, default=1500)
    args = parser.parse_args(argv)

    import asyncio

    return asyncio.run(_run(args.format, args.width, args.height))


if __name__ == "__main__":
    sys.exit(main())
