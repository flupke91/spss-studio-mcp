"""GGRAPH syntax generation from chart specs (P1).

Every builder returns a complete, chart-producing SPSS command.  Charts use
GGRAPH/GPL templates - clients describe *what* to plot, never the GPL itself.
Two procedures are templates too (their charts are captured by OMS the same
way): PPLOT for Q-Q plots and KM for Kaplan-Meier survival curves.
"""

from __future__ import annotations

from spss_mcp.chart_spec import (
    AreaSpec,
    BarErrorSpec,
    BarSpec,
    BoxplotSpec,
    ChartSpec,
    ErrorbarSpec,
    HistogramDensitySpec,
    HistogramSpec,
    KMCurveSpec,
    LineSpec,
    QQPlotSpec,
    ScatterSpec,
)


def _gpl_data_line(name: str, var: str, category: bool = False) -> str:
    """Emit a GPL DATA line for one variable."""
    if category:
        return f'  DATA: {name}=col(source(s), name("{var}"), unit.category())'
    return f'  DATA: {name}=col(source(s), name("{var}"))'


def _guides(spec: ChartSpec) -> list[str]:
    """Build GUIDE lines for labels and title."""
    lines: list[str] = []
    if spec.title:
        lines.append(f'  GUIDE: text.title(label("{spec.title}"))')
    if spec.x_label:
        lines.append(f'  GUIDE: axis(dim(1), label("{spec.x_label}"))')
    if spec.y_label:
        lines.append(f'  GUIDE: axis(dim(2), label("{spec.y_label}"))')
    return lines


def _ggraph(
    variables: list[str],
    gpl_body: list[str],
    spec: ChartSpec,
    dataset_vars: list[str] | None = None,
) -> str:
    var_decl = "VARIABLES=" + " ".join(
        dataset_vars if dataset_vars is not None else variables
    )
    guides = _guides(spec)
    lines = [
        "GGRAPH",
        f'  /GRAPHDATASET NAME="graphdataset" {var_decl}',
        "  /GRAPHSPEC SOURCE=INLINE.",
        "BEGIN GPL",
        '  SOURCE: s=userSource(id("graphdataset"))',
        *gpl_body,
        *guides,
        "END GPL.",
    ]
    return "\n".join(lines) + "\n"


def build_histogram_syntax(spec: HistogramSpec) -> str:
    var = spec.variable
    body = [
        f'  DATA: {var}=col(source(s), name("{var}"))',
        f"  ELEMENT: interval(position(summary.count({var})),",
        f"           shape.interior(shape.square), color.interior(color.{spec.color}))",
    ]
    return _ggraph([var], body, spec)


def build_scatter_syntax(spec: ScatterSpec) -> str:
    body = [
        f'  DATA: x=col(source(s), name("{spec.x}"))',
        f'  DATA: y=col(source(s), name("{spec.y}"))',
        "  ELEMENT: point(position(x*y),",
        f"           color.exterior(color.{spec.color}))",
    ]
    return _ggraph([spec.x, spec.y], body, spec)


def build_bar_syntax(spec: BarSpec) -> str:
    func = "SUM" if spec.stat == "sum" else "MEAN"
    agg_name = f"{func}_{spec.value}"
    dataset_vars = [spec.category, f'{func}({spec.value})[name="{agg_name}"]']
    body = [
        f'  DATA: cat=col(source(s), name("{spec.category}"), unit.category())',
        f'  DATA: agg=col(source(s), name("{agg_name}"))',
        "  ELEMENT: interval(position(cat*agg),",
        f"           shape.interior(shape.square), color.interior(color.{spec.color}))",
    ]
    return _ggraph([spec.category, spec.value], body, spec, dataset_vars=dataset_vars)


def build_line_syntax(spec: LineSpec) -> str:
    body = [
        f'  DATA: x=col(source(s), name("{spec.x}"))',
        f'  DATA: y=col(source(s), name("{spec.y}"))',
        "  ELEMENT: line(position(x*y),",
        f"           color.interior(color.{spec.color}))",
    ]
    return _ggraph([spec.x, spec.y], body, spec)


def _ci_percent(ci: float) -> int:
    """Convert a confidence level (0.95) to the MEANCI percent SPSS wants."""
    percent = round(ci * 100)
    if not 50 <= percent <= 99:
        raise ValueError(f"ci must be between 0.50 and 0.99, got {ci}")
    return percent


def _meanci_interval_syntax(
    category: str,
    value: str,
    ci: float,
    spec: ChartSpec,
    with_bar_shape: bool,
) -> str:
    """Shared GPL for error bars / bars with error bars (MEANCI precompute)."""
    percent = _ci_percent(ci)
    agg_name = f"MEANCI_{value}"
    dataset_vars = [f'MEANCI({value} {percent})[name="{agg_name}"]', category]
    shape = "shape.interior(shape.square), " if with_bar_shape else ""
    body = [
        f'  DATA: {agg_name}=col(source(s), name("{agg_name}"))',
        f'  DATA: cat=col(source(s), name("{category}"), unit.category())',
        "  ELEMENT: interval(position(cat*" + agg_name + "),",
        f"           {shape}color.interior(color.{spec.color}))",
        "  SCALE: linear(dim(2), include(0))",
    ]
    return _ggraph([category, value], body, spec, dataset_vars=dataset_vars)


def _title_command(spec: ChartSpec) -> str:
    """Return an SPSS TITLE command when the spec carries a title."""
    return f"TITLE '{spec.title}'.\n" if spec.title else ""


def build_boxplot_syntax(spec: BoxplotSpec) -> str:
    """Box-and-whisker plot via EXAMINE (traditional chart).

    GGRAPH's ``ELEMENT: schema`` was rejected by SPSS 32 on real datasets
    with ``outlier was found inside fences`` (cases whose value lies exactly
    on a fence), and its DOCX/EMF export produced zero-byte images.  The
    EXAMINE boxplot is captured by the same OMS pipeline and works for both
    PNG/TIFF and EMF exports.
    """
    var = spec.variable
    group = f" BY {spec.category}" if spec.category else ""
    return (
        _title_command(spec)
        + f"EXAMINE VARIABLES={var}{group}\n"
        + "  /PLOT BOXPLOT\n"
        + "  /STATISTICS NONE\n"
        + "  /NOTOTAL.\n"
    )


def build_errorbar_syntax(spec: ErrorbarSpec) -> str:
    return _meanci_interval_syntax(
        spec.category, spec.value, spec.ci, spec, with_bar_shape=False
    )


def build_qqplot_syntax(spec: QQPlotSpec) -> str:
    return _title_command(spec) + (
        "PPLOT\n"
        f"  /VARIABLES={spec.variable}\n"
        "  /NOLOG\n"
        "  /NOSTANDARDIZE\n"
        "  /TYPE=Q-Q\n"
        "  /FRACTION=BLOM\n"
        "  /TIES=MEAN.\n"
    )


def build_km_curve_syntax(spec: KMCurveSpec) -> str:
    group_part = f" BY {spec.group}" if spec.group else ""
    return _title_command(spec) + (
        f"KM {spec.time}{group_part}\n"
        f"  /STATUS={spec.status}({spec.event})\n"
        "  /PLOT SURVIVAL\n"
        "  /PRINT NONE.\n"
    )


def build_area_syntax(spec: AreaSpec) -> str:
    body = [
        f'  DATA: x=col(source(s), name("{spec.x}"))',
        f'  DATA: y=col(source(s), name("{spec.y}"))',
        "  ELEMENT: area(position(x*y),",
        f"           color.interior(color.{spec.color}))",
    ]
    return _ggraph([spec.x, spec.y], body, spec)


def build_histogram_density_syntax(spec: HistogramDensitySpec) -> str:
    var = spec.variable
    body = [
        f'  DATA: {var}=col(source(s), name("{var}"))',
        "  ELEMENT: interval(position(summary.count(bin.rect(" + var + "))),",
        f"           shape.interior(shape.square), color.interior(color.{spec.color}))",
        "  ELEMENT: line(position(density.normal(" + var + ")),",
        f"           color.interior(color.{spec.density_color}))",
    ]
    return _ggraph([var], body, spec)


def build_bar_error_syntax(spec: BarErrorSpec) -> str:
    return _meanci_interval_syntax(
        spec.category, spec.value, spec.ci, spec, with_bar_shape=True
    )


def build_chart_syntax(spec: ChartSpec) -> str:
    """Dispatch a spec to its chart builder (GGRAPH, PPLOT, or KM)."""
    if isinstance(spec, HistogramSpec):
        return build_histogram_syntax(spec)
    if isinstance(spec, ScatterSpec):
        return build_scatter_syntax(spec)
    if isinstance(spec, BarSpec):
        return build_bar_syntax(spec)
    if isinstance(spec, LineSpec):
        return build_line_syntax(spec)
    if isinstance(spec, BoxplotSpec):
        return build_boxplot_syntax(spec)
    if isinstance(spec, ErrorbarSpec):
        return build_errorbar_syntax(spec)
    if isinstance(spec, QQPlotSpec):
        return build_qqplot_syntax(spec)
    if isinstance(spec, KMCurveSpec):
        return build_km_curve_syntax(spec)
    if isinstance(spec, AreaSpec):
        return build_area_syntax(spec)
    if isinstance(spec, HistogramDensitySpec):
        return build_histogram_density_syntax(spec)
    if isinstance(spec, BarErrorSpec):
        return build_bar_error_syntax(spec)
    raise TypeError(f"Unsupported chart spec: {type(spec).__name__}")
