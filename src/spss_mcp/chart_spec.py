"""Chart specification models for the paper-ready chart pipeline (P1).

A ``ChartSpec`` describes a chart *declaratively*; the GGRAPH syntax is
generated from the spec by :mod:`spss_mcp.chart_templates`.  Charts are
always built from templates - free-form GGRAPH syntax is intentionally not
accepted from clients so the LLM cannot emit malformed GPL.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

ImageFormat = Literal["PNG", "TIFF", "EMF"]
ChartKind = Literal["histogram", "scatter", "bar", "line"]


class ChartSpec(BaseModel):
    """Base fields shared by every chart spec."""

    kind: ChartKind
    title: Optional[str] = Field(default=None, description="Chart title text")
    x_label: Optional[str] = Field(default=None, description="X axis label")
    y_label: Optional[str] = Field(default=None, description="Y axis label")


class HistogramSpec(ChartSpec):
    """Histogram of a single continuous variable."""

    kind: Literal["histogram"] = "histogram"
    variable: str = Field(description="Continuous variable to bin")
    color: str = Field(default="darkgray", description="GPL named fill color")


class ScatterSpec(ChartSpec):
    """Scatter plot of two continuous variables."""

    kind: Literal["scatter"] = "scatter"
    x: str = Field(description="X variable")
    y: str = Field(description="Y variable")
    color: str = Field(default="steelblue", description="GPL named point color")


class BarSpec(ChartSpec):
    """Bar chart of a categorical variable against a summary statistic of a
    continuous variable (mean by default)."""

    kind: Literal["bar"] = "bar"
    category: str = Field(description="Categorical variable for the X axis")
    value: str = Field(description="Continuous variable summarized per category")
    stat: Literal["mean", "sum"] = Field(
        default="mean", description="Summary statistic for bar height"
    )
    color: str = Field(default="darkgray", description="GPL named fill color")


class LineSpec(ChartSpec):
    """Line chart of a continuous variable against a time/ordinal variable."""

    kind: Literal["line"] = "line"
    x: str = Field(description="X (typically time) variable")
    y: str = Field(description="Y variable")
    color: str = Field(default="steelblue", description="GPL named line color")


SPEC_BY_KIND: dict[str, type[ChartSpec]] = {
    "histogram": HistogramSpec,
    "scatter": ScatterSpec,
    "bar": BarSpec,
    "line": LineSpec,
}


def build_spec(kind: str, **kwargs) -> ChartSpec:
    """Instantiate the spec model matching ``kind``."""
    try:
        return SPEC_BY_KIND[kind](**kwargs)
    except KeyError:
        raise ValueError(f"Unsupported chart kind: {kind}") from None
