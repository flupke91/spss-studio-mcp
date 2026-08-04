from pathlib import Path

import pytest

from spss_mcp.oms_image import (
    build_oms_image_block,
    find_image_files,
    oms_image_end_block,
    validate_image,
)


def test_build_oms_image_block():
    block = build_oms_image_block(
        output_dir=r"C:\temp\charts",
        imageroot="histogram_abc",
        image_format="PNG",
        width_px=1950,
        height_px=1500,
    )
    assert "/TAG='IMG1' /SELECT CHARTS" in block
    assert "FORMAT=IMAGE" in block
    assert "IMAGEFORMAT=PNG" in block
    assert "OUTFILE='C:/temp/charts'" in block
    assert "IMAGEROOT='histogram_abc'" in block
    assert "IMAGEWIDTH=1950" in block
    assert "IMAGEHEIGHT=1500" in block
    assert "IMAGETYPE=TRUE" in block


def test_unsupported_format_raises():
    with pytest.raises(ValueError):
        build_oms_image_block("C:/tmp", "root", image_format="GIF")


def test_oms_image_end_block():
    assert oms_image_end_block() == "OMSEND TAG='IMG1'.\n"


def test_find_image_files(tmp_path):
    (tmp_path / "scatter_001.png").write_bytes(b"x")
    (tmp_path / "scatter_002.png").write_bytes(b"x")
    (tmp_path / "other_001.png").write_bytes(b"x")
    files = find_image_files(tmp_path, "scatter")
    assert [f.name for f in files] == ["scatter_001.png", "scatter_002.png"]


def test_validate_image_ok(tmp_path):
    from PIL import Image

    png = tmp_path / "chart.png"
    Image.new("RGB", (200, 150), "white").save(png)
    meta = validate_image(png, expected_format="PNG", dpi=300)
    assert meta["width"] == 200
    assert meta["height"] == 150
    assert meta["format"] == "PNG"
    assert meta["dpi"] == 300


def test_validate_image_missing(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        validate_image(tmp_path / "nope.png")


def test_validate_image_empty(tmp_path):
    empty = tmp_path / "empty.png"
    empty.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        validate_image(empty)


def test_validate_image_wrong_format(tmp_path):
    from PIL import Image

    jpg = tmp_path / "chart.jpg"
    Image.new("RGB", (200, 150), "white").save(jpg, format="JPEG")
    with pytest.raises(ValueError, match="Unexpected image format"):
        validate_image(jpg, expected_format="PNG")
