"""P3/P4 completion: verify the remaining tools against the real machine.

Covers the file utilities, status/validation/structured tools, and the
registry method ``spss_genlin`` that were not part of the 26-case method
verification.  Chart TIFF coverage is run via ``poc_chart --format TIFF``.

Usage:
    python scripts/tool_verification.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

import pandas as pd
import pyreadstat

from spss_mcp import server
from spss_mcp.spss_engine import get_engine

EX = Path(__file__).resolve().parents[1] / "examples" / "data"
OUT = Path(__file__).resolve().parents[1] / "docs" / "tool_verification.json"

SURVEY = str(EX / "survey_study.sav")


async def run_case(name: str, coro) -> dict:
    started = time.perf_counter()
    try:
        output = await coro
    except Exception as exc:  # pragma: no cover
        return {
            "case": name,
            "ok": False,
            "error": f"exception: {exc}",
            "seconds": round(time.perf_counter() - started, 1),
            "marker_hit": False,
        }
    elapsed = round(time.perf_counter() - started, 1)
    failed = str(output).strip().startswith("Error:")
    return {
        "case": name,
        "ok": not failed,
        "error": None if not failed else str(output).strip().splitlines()[0][:160],
        "seconds": elapsed,
        "marker_hit": not failed,
    }


async def build_cases() -> list[dict]:
    cases = []

    # --- file utilities (no engine needed, but real .sav data) ---
    cases.append(("read_data", server.spss_read_data(file_path=SURVEY, max_rows=5)))
    cases.append(("file_summary", server.spss_file_summary(file_path=SURVEY)))
    cases.append(
        ("list_variables", server.spss_list_variables(file_path=SURVEY, search="q"))
    )
    cases.append(("read_metadata", server.spss_read_metadata(file_path=SURVEY)))
    cases.append(("list_files", server.spss_list_files(directory=str(EX))))

    # --- status / validation / structured / run_syntax ---
    cases.append(("check_status", server.spss_check_status(ctx=None)))
    cases.append(
        (
            "validate_syntax",
            server.spss_validate_syntax(syntax="FREQUENCIES VARIABLES=gender.\n"),
        )
    )
    cases.append(
        (
            "structured_result",
            server.spss_structured_result(
                syntax="FREQUENCIES VARIABLES=gender.\n",
                data_file=SURVEY,
                save_viewer_output=False,
                save_syntax_file=False,
            ),
        )
    )
    cases.append(
        (
            "run_syntax_full",
            server.spss_run_syntax(
                syntax="FREQUENCIES VARIABLES=gender.\n",
                data_file=SURVEY,
                save_viewer_output=True,
                save_syntax_file=True,
            ),
        )
    )

    # --- registry method not covered by the 26-case matrix ---
    cases.append(
        (
            "genlin",
            server.spss_genlin(
                file_path=str(
                    Path(__file__).resolve().parents[1]
                    / "examples"
                    / "data"
                    / "mediation_study.sav"
                ),
                dependent="performance",
                predictors=["autonomy", "satisfaction"],
                distribution="NORMAL",
            ),
        )
    )

    return cases


async def main() -> int:
    cases = await build_cases()
    engine = get_engine()
    ok, msg = await engine.ensure_started()
    print(f"engine start: {ok} - {msg}")
    if not ok:
        return 1

    # import_csv: write a small CSV, import it, then clean up
    csv_path = Path.home() / "spss_studio_mcp_sample.csv"
    out_sav = Path.home() / "spss_studio_mcp_sample.sav"
    try:
        df, _ = pyreadstat.read_sav(SURVEY)
        df.head(20).to_csv(csv_path, index=False)
        results = []
        import_csv_res = await run_case(
            "import_csv",
            server.spss_import_csv(csv_path=str(csv_path), output_path=str(out_sav)),
        )
        results.append(import_csv_res)
        print(
            f"[{'OK ' if import_csv_res['ok'] else 'FAIL'}] import_csv {import_csv_res['seconds']:>5}s {import_csv_res.get('error') or ''}"
        )
    finally:
        csv_path.unlink(missing_ok=True)
        out_sav.unlink(missing_ok=True)

    for name, coro in cases:
        res = await run_case(name, coro)
        results.append(res)
        status = "OK " if res["ok"] else "FAIL"
        print(f"[{status}] {res['case']:<22} {res['seconds']:>5}s {res['error'] or ''}")

    await engine.stop()
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    failed = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed -> {OUT}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
