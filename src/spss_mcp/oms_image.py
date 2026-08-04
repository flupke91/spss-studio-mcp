"""OMS IMAGE export and image post-processing (P1).

Turns a chart-producing SPSS command (e.g. GGRAPH) into a paper-ready image
file.  ``build_oms_image_block`` wraps the command in an OMS IMAGE block that
emits PNG/TIFF/EMF; ``validate_image`` checks the produced file with Pillow
and (for PNG) rewrites the DPI metadata so journal requirements are met.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from spss_mcp.chart_spec import ImageFormat

IMAGE_FORMATS: tuple[str, ...] = ("PNG", "TIFF", "EMF")


def build_oms_image_block(
    output_dir: str,
    imageroot: str,
    image_format: ImageFormat = "PNG",
    width_px: int = 1950,
    height_px: int = 1500,
) -> str:
    """Return the OMS block that exports produced charts to image files.

    ``imageroot`` is used as the base filename; SPSS appends a sequence
    suffix (``<imageroot>_001.png`` etc.) inside ``output_dir``.
    """
    fmt = image_format.upper()
    if fmt not in IMAGE_FORMATS:
        raise ValueError(f"Unsupported image format: {image_format}")
    out_fwd = output_dir.replace("\\", "/")
    return (
        "OMS /TAG='IMG1' /SELECT CHARTS\n"
        "  /DESTINATION FORMAT=IMAGE\n"
        f"    IMAGEFORMAT={fmt}\n"
        f"    OUTFILE='{out_fwd}'\n"
        f"    IMAGEROOT='{imageroot}'\n"
        f"    IMAGEWIDTH={width_px}\n"
        f"    IMAGEHEIGHT={height_px}\n"
        "    IMAGETYPE=TRUE.\n"
    )


def oms_image_end_block() -> str:
    """Return the OMSEND matching the IMG1 tag."""
    return "OMSEND TAG='IMG1'.\n"


def find_image_files(output_dir: Path, imageroot: str) -> list[Path]:
    """Return produced image files matching ``imageroot`` inside the dir."""
    pattern = f"{imageroot}*"
    return sorted(
        p
        for p in output_dir.glob(pattern)
        if p.suffix.lower() in {".png", ".tif", ".tiff", ".emf"}
    )


def validate_image(
    path: Path,
    expected_format: str = "PNG",
    min_width: int = 100,
    min_height: int = 100,
    dpi: int = 300,
) -> dict:
    """Validate an exported chart image with Pillow.

    Returns metadata; raises ``ValueError`` when the file is missing, empty,
    unreadable, or smaller than the minimum dimensions.  For PNG the DPI
    metadata is rewritten to the requested value (post-processing step).
    """
    if not path.exists():
        raise ValueError(f"Image file not found: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Image file is empty: {path}")

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise ValueError("Pillow is required for image validation") from exc

    try:
        with Image.open(path) as img:
            width, height = img.size
            fmt = (img.format or "").upper()
        if width < min_width or height < min_height:
            raise ValueError(
                f"Image too small: {width}x{height} (min {min_width}x{min_height})"
            )
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Unreadable image file {path}: {exc}") from exc

    if fmt != expected_format.upper():
        raise ValueError(f"Unexpected image format: {fmt} (expected {expected_format})")

    # Rewrite DPI metadata for PNG so journals see a 300dpi bitmap.
    if fmt == "PNG" and dpi:
        with Image.open(path) as img:
            img.save(path, format="PNG", dpi=(dpi, dpi))

    return {
        "path": str(path),
        "format": fmt,
        "width": width,
        "height": height,
        "bytes": path.stat().st_size,
        "dpi": dpi,
    }
