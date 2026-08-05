import pytest

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
    build_spec,
)
from spss_mcp.chart_templates import (
    build_bar_error_syntax,
    build_bar_syntax,
    build_boxplot_syntax,
    build_chart_syntax,
    build_errorbar_syntax,
    build_histogram_density_syntax,
    build_histogram_syntax,
    build_km_curve_syntax,
    build_line_syntax,
    build_qqplot_syntax,
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
    assert 'MEAN(score)[name="MEAN_score"]' in mean
    assert "position(cat*agg)" in mean
    total = build_bar_syntax(BarSpec(category="group", value="score", stat="sum"))
    assert 'SUM(score)[name="SUM_score"]' in total


def test_line_syntax_uses_interior_color():
    syntax = build_line_syntax(LineSpec(x="time", y="value"))
    assert "color.interior(color.steelblue)" in syntax


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


def test_boxplot_syntax_with_group():
    syntax = build_boxplot_syntax(
        BoxplotSpec(variable="score", category="group", title="Box")
    )
    assert "EXAMINE VARIABLES=score BY group" in syntax
    assert "/PLOT BOXPLOT" in syntax
    assert "/STATISTICS NONE" in syntax
    assert "/NOTOTAL" in syntax
    assert "TITLE 'Box'." in syntax


def test_boxplot_syntax_single_variable():
    syntax = build_boxplot_syntax(BoxplotSpec(variable="score"))
    assert "EXAMINE VARIABLES=score" in syntax
    assert " BY " not in syntax
    assert "/PLOT BOXPLOT" in syntax


def test_errorbar_syntax_precomputes_meanci():
    syntax = build_errorbar_syntax(
        ErrorbarSpec(category="group", value="score", ci=0.95)
    )
    assert 'MEANCI(score 95)[name="MEANCI_score"]' in syntax
    assert "ELEMENT: interval(position(cat*MEANCI_score)" in syntax
    assert "SCALE: linear(dim(2), include(0))" in syntax


def test_errorbar_invalid_ci_raises():
    with pytest.raises(ValueError, match="ci"):
        build_errorbar_syntax(ErrorbarSpec(category="group", value="score", ci=0.30))


def test_qqplot_syntax():
    syntax = build_qqplot_syntax(QQPlotSpec(variable="score", title="QQ"))
    assert "TITLE 'QQ'." in syntax
    assert "PPLOT" in syntax
    assert "/VARIABLES=score" in syntax
    assert "/TYPE=Q-Q" in syntax


def test_km_curve_syntax_with_group():
    syntax = build_km_curve_syntax(
        KMCurveSpec(time="time", status="status", event=1, group="group")
    )
    assert "KM time BY group" in syntax
    assert "/STATUS=status(1)" in syntax
    assert "/PLOT SURVIVAL" in syntax


def test_km_curve_syntax_without_group():
    syntax = build_km_curve_syntax(KMCurveSpec(time="time", status="status", event=1))
    assert "KM time" in syntax
    assert "BY" not in syntax


def test_area_syntax():
    syntax = build_chart_syntax(AreaSpec(x="x", y="y"))
    assert "ELEMENT: area(position(x*y)" in syntax


def test_histogram_density_syntax():
    syntax = build_histogram_density_syntax(
        build_spec("histogram_density", variable="score")
    )
    assert "density.normal(score)" in syntax
    assert "summary.count(bin.rect(score))" in syntax


def test_bar_error_syntax():
    syntax = build_bar_error_syntax(BarErrorSpec(category="group", value="score"))
    assert 'MEANCI(score 95)[name="MEANCI_score"]' in syntax
    assert "shape.interior(shape.square)" in syntax


def test_dispatch_all_kinds():
    for kind in (
        "histogram",
        "scatter",
        "bar",
        "line",
        "boxplot",
        "errorbar",
        "qqplot",
        "km_curve",
        "area",
        "histogram_density",
        "bar_error",
    ):
        kwargs = {
            "histogram": dict(variable="score"),
            "scatter": dict(x="x", y="y"),
            "bar": dict(category="group", value="score"),
            "line": dict(x="x", y="y"),
            "boxplot": dict(variable="score", category="group"),
            "errorbar": dict(category="group", value="score"),
            "qqplot": dict(variable="score"),
            "km_curve": dict(time="time", status="status"),
            "area": dict(x="x", y="y"),
            "histogram_density": dict(variable="score"),
            "bar_error": dict(category="group", value="score"),
        }[kind]
        syntax = build_chart_syntax(build_spec(kind, **kwargs))
        assert syntax.endswith("\n")
        assert syntax.strip()
