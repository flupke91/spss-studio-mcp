"""Chart export orchestration (P1).

Ties together chart specs, GGRAPH templates, the SPSS execution engine and
the OMS exporter.  ``export_chart`` is the single entry point used by the
``spss_chart_*`` tools and the PoC runner.

Export strategy on SPSS 32 (verified): charts are captured with
``OMS FORMAT=HTML`` (raster: base64 PNG embedded in HTML, extracted and
post-processed) or ``OMS FORMAT=DOC`` (vector: EMF files inside the DOCX zip).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Awaitable, Callable, Optional

from spss_mcp.chart_spec import ChartSpec, ImageFormat
from spss_mcp.chart_templates import build_chart_syntax
from spss_mcp.config import get_results_dir
from spss_mcp.oms_image import (
    build_oms_doc_block,
    build_oms_image_block,
    extract_docx_emf,
    extract_html_images,
    oms_doc_end_block,
    oms_image_end_block,
    validate_emf,
    validate_image,
)

DEFAULT_WIDTH_PX = 1950  # 6.5in * 300dpi (US letter text width)
DEFAULT_HEIGHT_PX = 1500  # 5in * 300dpi
DEFAULT_DPI = 300


def _build_export_syntax(
    spec: ChartSpec,
    output_root: str,
    image_format: ImageFormat,
) -> str:
    chart_syntax = build_chart_syntax(spec).rstrip() + "\n"
    if image_format.upper() == "EMF":
        block = build_oms_doc_block(f"{output_root}.docx")
        end_block = oms_doc_end_block()
    else:
        block = build_oms_image_block(f"{output_root}.html", image_format=image_format)
        end_block = oms_image_end_block()
    return block + chart_syntax + end_block


def _convert_png_to_tiff(png_path: Path, dpi: int) -> Path:
    """Convert a post-processed PNG chart to LZW-compressed TIFF at DPI."""
    from PIL import Image

    tiff_path = png_path.with_suffix(".tiff")
    with Image.open(png_path) as img:
        img.save(tiff_path, format="TIFF", dpi=(dpi, dpi), compression="tiff_lzw")
    png_path.unlink(missing_ok=True)
    return tiff_path


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
    output_root = str(get_results_dir() / imageroot)
    syntax = _build_export_syntax(spec, output_root, image_format)
    result = await runner(syntax, data_file=data_file)

    fmt = image_format.upper()
    try:
        if fmt == "EMF":
            files = extract_docx_emf(Path(f"{output_root}.docx"), imageroot)
        else:
            files = extract_html_images(Path(f"{output_root}.html"), imageroot)
    except (ValueError, OSError) as exc:
        error = result.get("error") or str(exc)
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
            if fmt == "EMF":
                meta = validate_emf(image_path)
            else:
                meta = validate_image(
                    image_path,
                    expected_format="PNG",
                    dpi=dpi,
                    target_width=width_px,
                    target_height=height_px,
                )
                if fmt == "TIFF":
                    tiff_path = _convert_png_to_tiff(Path(meta["path"]), dpi)
                    meta["path"] = str(tiff_path)
                    meta["format"] = "TIFF"
                    meta["bytes"] = tiff_path.stat().st_size
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
