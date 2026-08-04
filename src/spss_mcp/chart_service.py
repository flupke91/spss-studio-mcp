"""Chart export orchestration (P1).

Ties together chart specs, GGRAPH templates, the SPSS execution engine and
the OMS IMAGE exporter.  ``export_chart`` is the single entry point used by
the ``spss_chart_*`` tools and the PoC runner.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Awaitable, Callable, Optional

from spss_mcp.chart_spec import ChartSpec, ImageFormat
from spss_mcp.chart_templates import build_chart_syntax
from spss_mcp.config import get_results_dir
from spss_mcp.oms_image import (
    build_oms_image_block,
    find_image_files,
    oms_image_end_block,
    validate_image,
)

DEFAULT_WIDTH_PX = 1950  # 6.5in * 300dpi (US letter text width)
DEFAULT_HEIGHT_PX = 1500  # 5in * 300dpi
DEFAULT_DPI = 300


def _build_export_syntax(
    spec: ChartSpec,
    imageroot: str,
    image_format: ImageFormat,
    width_px: int,
    height_px: int,
) -> str:
    chart_syntax = build_chart_syntax(spec)
    block = build_oms_image_block(
        output_dir=str(get_results_dir()),
        imageroot=imageroot,
        image_format=image_format,
        width_px=width_px,
        height_px=height_px,
    )
    return block + chart_syntax + oms_image_end_block()


async def export_chart(
    spec: ChartSpec,
    image_format: ImageFormat = "PNG",
    width_px: int = DEFAULT_WIDTH_PX,
    height_px: int = DEFAULT_HEIGHT_PX,
    dpi: int = DEFAULT_DPI,
    data_file: Optional[str] = None,
    run_syntax_fn: Optional[Callable[..., Awaitable[dict]]] = None,
) -> dict:
    """Export a chart spec to an image file and return its metadata.

    ``run_syntax_fn`` is injectable for tests; it defaults to the real engine.
    """
    from spss_mcp.spss_runner import run_syntax

    runner = run_syntax_fn or run_syntax
    imageroot = f"{spec.kind}_{uuid.uuid4().hex[:8]}"
    syntax = _build_export_syntax(spec, imageroot, image_format, width_px, height_px)
    result = await runner(syntax, data_file=data_file)

    files = find_image_files(get_results_dir(), imageroot)
    if not files:
        error = result.get("error") or "no image file was produced"
        return {
            "success": False,
            "error": error,
            "syntax": syntax,
            "imageroot": imageroot,
            "images": [],
            "spss": result,
        }

    image_meta = []
    for image_path in files:
        try:
            meta = validate_image(
                image_path,
                expected_format=image_format,
                dpi=dpi,
            )
            meta["success"] = True
        except ValueError as exc:
            meta = {"path": str(image_path), "success": False, "error": str(exc)}
        image_meta.append(meta)

    return {
        "success": True,
        "imageroot": imageroot,
        "images": image_meta,
        "syntax": syntax,
        "spss": result,
    }
