"""OMS chart export and image post-processing (P1).

SPSS 32 compatibility (verified on SPSS Statistics 32.0.0):

* ``OMS /DESTINATION FORMAT=IMAGE`` plus ``IMAGEROOT`` was removed from SPSS
  and is rejected with ``Unknown keyword or subcommand: IMAGE``.
* ``FORMAT=HTML IMAGES=YES OUTFILE=...`` is the supported raster path: SPSS
  writes the HTML file verbatim and embeds every chart as a base64
  ``data:image/png`` URI.  ``IMAGEFORMAT`` is ignored for HTML (TIFF/EMF still
  come back as PNG) and ``IMAGEWIDTH``/``IMAGEHEIGHT`` are rejected.
* ``FORMAT=DOC OUTFILE=...`` is the vector path: SPSS writes a ``.docx`` zip
  whose ``word/media/imageN.emf`` members are the charts as vector EMF.

This module wraps a chart command in the right OMS block and post-processes
the produced HTML/DOCX into standalone PNG/TIFF/EMF files.
"""

from __future__ import annotations

import base64
import re
import struct
import zipfile
from pathlib import Path
from typing import Optional

from spss_mcp.chart_spec import ImageFormat

IMAGE_FORMATS: tuple[str, ...] = ("PNG", "TIFF", "EMF")

_EMBEDDED_IMAGE_RE = re.compile(r"data:image/(\w+);base64,([A-Za-z0-9+/=]+)")
_DOCX_EMF_RE = re.compile(r"word/media/image\d+\.emf", re.IGNORECASE)


def build_oms_image_block(
    html_outfile: str,
    image_format: ImageFormat = "PNG",
) -> str:
    """Return the OMS HTML block that captures charts into an HTML file.

    SPSS 32 embeds each chart as a base64 PNG inside the HTML file written to
    ``html_outfile`` (used verbatim, no extension is appended).  ``IMAGEFORMAT``
    is accepted but ignored - HTML always embeds PNG regardless of the value.
    """
    fmt = image_format.upper()
    if fmt not in IMAGE_FORMATS:
        raise ValueError(f"Unsupported image format: {image_format}")
    out_fwd = html_outfile.replace("\\", "/")
    return (
        "OMS /TAG='IMG1' /SELECT CHARTS\n"
        "  /DESTINATION FORMAT=HTML\n"
        "    IMAGES=YES\n"
        f"    IMAGEFORMAT={fmt}\n"
        f"    OUTFILE='{out_fwd}'.\n"
    )


def build_oms_doc_block(docx_outfile: str) -> str:
    """Return the OMS DOC block that captures charts as vector EMF.

    SPSS 32 writes a ``.docx`` zip (``word/media/imageN.emf``) when OUTFILE has
    no extension; an explicit ``.doc`` suffix produces RTF instead.
    """
    out_fwd = docx_outfile.replace("\\", "/")
    return (
        "OMS /TAG='EMF1' /SELECT CHARTS\n"
        "  /DESTINATION FORMAT=DOC\n"
        f"    OUTFILE='{out_fwd}'.\n"
    )


def oms_image_end_block() -> str:
    """Return the OMSEND matching the IMG1 tag."""
    return "OMSEND TAG='IMG1'.\n"


def oms_doc_end_block() -> str:
    """Return the OMSEND matching the EMF1 tag used by the DOC block."""
    return "OMSEND TAG='EMF1'.\n"


def extract_html_images(html_path: Path, imageroot: str) -> list[Path]:
    """Decode charts embedded as base64 data URIs in an SPSS HTML export.

    Produces ``<imageroot>_001.png``, ``<imageroot>_002.png`` ... next to the
    HTML file and returns their paths.
    """
    if not html_path.exists():
        raise ValueError(f"HTML export not found: {html_path}")
    text = html_path.read_text(encoding="utf-8", errors="replace")
    uris = _EMBEDDED_IMAGE_RE.findall(text)
    if not uris:
        raise ValueError(f"No embedded chart image found in {html_path}")
    files: list[Path] = []
    for i, (fmt, b64) in enumerate(uris, start=1):
        ext = ".png" if fmt.lower() == "png" else f".{fmt.lower()}"
        out = html_path.parent / f"{imageroot}_{i:03d}{ext}"
        out.write_bytes(base64.b64decode(b64))
        files.append(out)
    return sorted(files)


def extract_docx_emf(docx_path: Path, imageroot: str) -> list[Path]:
    """Extract vector EMF charts from an SPSS DOCX export.

    Produces ``<imageroot>_001.emf``, ``<imageroot>_002.emf`` ... next to the
    DOCX file and returns their paths.  SPSS 32 writes zero-byte EMF members
    for boxplot (``schema``) charts; those are skipped and an explicit error
    is raised when no usable EMF remains.
    """
    if not docx_path.exists():
        raise ValueError(f"DOCX export not found: {docx_path}")
    with zipfile.ZipFile(docx_path) as zf:
        emf_names = sorted(
            info.filename
            for info in zf.infolist()
            if _DOCX_EMF_RE.fullmatch(info.filename)
        )
        files: list[Path] = []
        for i, name in enumerate(emf_names, start=1):
            raw = zf.read(name)
            if not raw:
                continue
            out = docx_path.parent / f"{imageroot}_{i:03d}.emf"
            out.write_bytes(raw)
            files.append(out)
    if not files:
        raise ValueError(
            "SPSS wrote empty EMF members for this chart type (known on SPSS 32 "
            "for boxplot/schema charts); request PNG or TIFF instead."
        )
    return sorted(files)


def find_image_files(output_dir: Path, imageroot: str) -> list[Path]:
    """Return produced image files matching ``imageroot`` inside the dir."""
    pattern = f"{imageroot}*"
    return sorted(
        p
        for p in output_dir.glob(pattern)
        if p.suffix.lower() in {".png", ".tif", ".tiff", ".emf"}
    )


def _resampling_lanczos():
    """Return Pillow's Lanczos resampling constant across versions."""
    from PIL import Image

    return getattr(Image, "Resampling", Image).LANCZOS


def validate_image(
    path: Path,
    expected_format: str = "PNG",
    min_width: int = 100,
    min_height: int = 100,
    dpi: int = 300,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
) -> dict:
    """Validate an exported chart image with Pillow.

    Returns metadata; raises ``ValueError`` when the file is missing, empty,
    unreadable, or smaller than the minimum dimensions.  When ``target_width``
    and ``target_height`` are given the image is resized (Lanczos) to that size
    first.  For PNG the DPI metadata is rewritten to the requested value.
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

    # Resize to the requested paper dimensions, then rewrite DPI metadata.
    if (
        target_width
        and target_height
        and (width != target_width or height != target_height)
    ):
        with Image.open(path) as img:
            img = img.convert("RGB") if img.mode != "RGB" else img
            img = img.resize((target_width, target_height), _resampling_lanczos())
            img.save(path, format="PNG", dpi=(dpi, dpi))
        width, height = target_width, target_height
    elif fmt == "PNG" and dpi:
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


def validate_emf(path: Path) -> dict:
    """Validate a vector EMF chart (ENHMETAHEADER magic + non-empty).

    Width/height are reported at 96 dpi from the EMF frame rectangle
    (stored in 0.01 mm units); the vector itself scales to any resolution.
    """
    if not path.exists():
        raise ValueError(f"EMF file not found: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"EMF file is empty: {path}")

    data = path.read_bytes()
    if len(data) < 44 or data[0:4] != b"\x01\x00\x00\x00" or data[40:44] != b" EMF":
        raise ValueError(f"Not a valid EMF file: {path}")

    left, top, right, bottom = struct.unpack("<4i", data[24:40])
    width_mm = (right - left) / 100.0
    height_mm = (bottom - top) / 100.0
    width = max(1, round(width_mm / 25.4 * 96))
    height = max(1, round(height_mm / 25.4 * 96))

    return {
        "path": str(path),
        "format": "EMF",
        "width": width,
        "height": height,
        "bytes": len(data),
        "dpi": 300,
    }
