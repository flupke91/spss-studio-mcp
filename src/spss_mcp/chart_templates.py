"""GGRAPH syntax generation from chart specs (P1).

Every builder returns a complete GGRAPH command for SPSS.  All charts go
through these templates - clients describe *what* to plot, never the GPL
itself, so malformed syntax cannot be produced by an LLM.
"""

from __future__ import annotations

from spss_mcp.chart_spec import (
    BarSpec,
    ChartSpec,
    HistogramSpec,
    LineSpec,
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


def _ggraph(variables: list[str], gpl_body: list[str], spec: ChartSpec) -> str:
    var_decl = " ".join(f"VARIABLES={v}" for v in variables)
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
    return "\n".join(lines)


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
    stat = "sum" if spec.stat == "sum" else "mean"
    body = [
        f'  DATA: cat=col(source(s), name("{spec.category}"), unit.category())',
        f'  DATA: val=col(source(s), name("{spec.value}"))',
        "  ELEMENT: interval(position(cat*summary." + stat + "(val)),",
        f"           shape.interior(shape.square), color.interior(color.{spec.color}))",
    ]
    return _ggraph([spec.category, spec.value], body, spec)


def build_line_syntax(spec: LineSpec) -> str:
    body = [
        f'  DATA: x=col(source(s), name("{spec.x}"))',
        f'  DATA: y=col(source(s), name("{spec.y}"))',
        "  ELEMENT: line(position(x*y),",
        f"           color.exterior(color.{spec.color}))",
    ]
    return _ggraph([spec.x, spec.y], body, spec)


def build_chart_syntax(spec: ChartSpec) -> str:
    """Dispatch a spec to its GGRAPH builder."""
    if isinstance(spec, HistogramSpec):
        return build_histogram_syntax(spec)
    if isinstance(spec, ScatterSpec):
        return build_scatter_syntax(spec)
    if isinstance(spec, BarSpec):
        return build_bar_syntax(spec)
    if isinstance(spec, LineSpec):
        return build_line_syntax(spec)
    raise TypeError(f"Unsupported chart spec: {type(spec).__name__}")
