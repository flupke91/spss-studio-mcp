"""P1 PoC: GGRAPH -> OMS export -> PNG/EMF on a real SPSS install.

Run from the repo root:
    python scripts/poc_chart_pipeline.py

Verified on SPSS Statistics 32.0.0: ``OMS FORMAT=IMAGE`` / ``IMAGEROOT`` were
removed, so charts are captured via ``FORMAT=HTML`` (base64 PNG embedded in
the HTML) or ``FORMAT=DOC`` (vector EMF inside the DOCX zip).
"""

import asyncio
import sys
from pathlib import Path

from spss_mcp.config import get_results_dir
from spss_mcp.oms_image import (
    extract_docx_emf,
    extract_html_images,
    validate_emf,
    validate_image,
)
from spss_mcp.spss_engine import get_engine
from spss_mcp.spss_runner import run_syntax

SAMPLE_DATA = """
INPUT PROGRAM.
LOOP #i = 1 TO 200.
  COMPUTE score = RV.NORMAL(50, 10).
  COMPUTE group = MOD(#i, 3).
  END CASE.
END LOOP.
END FILE.
END INPUT PROGRAM.
EXECUTE.
"""

CHART_SYNTAX = """
GGRAPH
  /GRAPHDATASET NAME="graphdataset" VARIABLES=score
  /GRAPHSPEC SOURCE=INLINE.
BEGIN GPL
  SOURCE: s=userSource(id("graphdataset"))
  DATA: score=col(source(s), name("score"))
  GUIDE: axis(dim(1), label("Score"))
  GUIDE: axis(dim(2), label("Frequency"))
  ELEMENT: interval(position(summary.count(bin.rect(score))), shape.interior(shape.square))
END GPL.
"""

TARGET_WIDTH = 1950
TARGET_HEIGHT = 1500
DPI = 300


async def run_variant(name: str, block: str, tag: str) -> bool:
    syntax = SAMPLE_DATA + block + CHART_SYNTAX + f"OMSEND TAG='{tag}'.\n"
    result = await run_syntax(
        syntax,
        data_file=None,
        save_viewer_output=False,
        save_syntax_file=False,
    )
    print(f"\n=== variant: {name} ===")
    print(f"err_level: {result.get('err_level')}")
    print(f"error: {result.get('error')}")
    print(f"warn: {result.get('warn')}")
    if result.get("error"):
        return False
    return True


async def main() -> None:
    results_dir = get_results_dir()
    results_dir.mkdir(parents=True, exist_ok=True)
    print(f"results dir: {results_dir}")

    engine = get_engine()
    ok, msg = await engine.ensure_started()
    print(f"engine start: {ok} - {msg}")
    if not ok:
        return 1

    failed = False
    ok = await run_variant(
        "html_raster_png",
        f"OMS /TAG='IMG1' /SELECT CHARTS\n"
        f"  /DESTINATION FORMAT=HTML\n    IMAGES=YES\n    IMAGEFORMAT=PNG\n"
        f"    OUTFILE='{(results_dir / 'poc_histogram').as_posix()}'.\n",
        "IMG1",
    )
    failed = failed or not ok
    if ok:
        html = results_dir / "poc_histogram"
        pngs = extract_html_images(html, "poc_histogram")
        for png in pngs:
            try:
                meta = validate_image(
                    png,
                    expected_format="PNG",
                    dpi=DPI,
                    target_width=TARGET_WIDTH,
                    target_height=TARGET_HEIGHT,
                )
                print(
                    f"[OK ] PNG {png.name}: {meta['width']}x{meta['height']} "
                    f"{meta['bytes']} bytes @ {meta['dpi']}dpi"
                )
            except ValueError as exc:
                print(f"[BAD] PNG {png.name}: {exc}")
                failed = True

    ok = await run_variant(
        "docx_vector_emf",
        f"OMS /TAG='EMF1' /SELECT CHARTS\n"
        f"  /DESTINATION FORMAT=DOC\n"
        f"    OUTFILE='{(results_dir / 'poc_histogram_emf').as_posix()}'.\n",
        "EMF1",
    )
    failed = failed or not ok
    if ok:
        docx = results_dir / "poc_histogram_emf.docx"
        emfs = extract_docx_emf(docx, "poc_histogram_emf")
        for emf in emfs:
            try:
                meta = validate_emf(emf)
                print(
                    f"[OK ] EMF {emf.name}: {meta['width']}x{meta['height']} "
                    f"@96dpi, {meta['bytes']} bytes (vector)"
                )
            except ValueError as exc:
                print(f"[BAD] EMF {emf.name}: {exc}")
                failed = True

    await engine.stop()
    print("\n" + ("FAILED" if failed else "ALL VARIANTS OK"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
