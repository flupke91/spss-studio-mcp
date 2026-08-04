from spss_mcp.chart_spec import (
    BarSpec,
    HistogramSpec,
    LineSpec,
    ScatterSpec,
    build_spec,
)
from spss_mcp.chart_templates import (
    build_bar_syntax,
    build_chart_syntax,
    build_histogram_syntax,
    build_line_syntax,
    build_scatter_syntax,
)


def test_histogram_syntax():
    syntax = build_histogram_syntax(
        HistogramSpec(
            variable="score",
            title="Histogram of score",
            x_label="Score",
            y_label="Frequency",
        )
    )
    assert "GGRAPH" in syntax
    assert 'GRAPHDATASET NAME="graphdataset" VARIABLES=score' in syntax
    assert "ELEMENT: interval(position(summary.count(score))" in syntax
    assert 'GUIDE: text.title(label("Histogram of score"))' in syntax
    assert 'GUIDE: axis(dim(1), label("Score"))' in syntax
    assert 'GUIDE: axis(dim(2), label("Frequency"))' in syntax


def test_scatter_syntax():
    syntax = build_scatter_syntax(ScatterSpec(x="x", y="y"))
    assert 'DATA: x=col(source(s), name("x"))' in syntax
    assert 'DATA: y=col(source(s), name("y"))' in syntax
    assert "ELEMENT: point(position(x*y)" in syntax


def test_bar_syntax_mean_and_sum():
    mean = build_bar_syntax(BarSpec(category="group", value="score"))
    assert "position(cat*summary.mean(val))" in mean
    total = build_bar_syntax(BarSpec(category="group", value="score", stat="sum"))
    assert "position(cat*summary.sum(val))" in total


def test_line_syntax():
    syntax = build_line_syntax(LineSpec(x="time", y="value"))
    assert "ELEMENT: line(position(x*y)" in syntax


def test_build_chart_syntax_dispatch():
    spec = build_spec("scatter", x="a", y="b")
    syntax = build_chart_syntax(spec)
    assert "ELEMENT: point(position(x*y)" in syntax


def test_unsupported_kind_raises():
    import pytest

    with pytest.raises(ValueError):
        build_spec("pie")
