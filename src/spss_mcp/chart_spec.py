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
ChartKind = Literal[
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
]


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


class BoxplotSpec(ChartSpec):
    """Box-and-whisker plot of a continuous variable, optionally per category."""

    kind: Literal["boxplot"] = "boxplot"
    variable: str = Field(description="Continuous variable to summarise")
    category: Optional[str] = Field(
        default=None, description="Optional categorical variable for the X axis"
    )
    color: str = Field(default="darkgray", description="GPL named fill color")


class ErrorbarSpec(ChartSpec):
    """Mean with confidence-interval error bars per category."""

    kind: Literal["errorbar"] = "errorbar"
    category: str = Field(description="Categorical variable for the X axis")
    value: str = Field(description="Continuous variable summarised per category")
    ci: float = Field(
        default=0.95, description="Confidence level, e.g. 0.95 for 95% CI"
    )
    color: str = Field(default="darkgray", description="GPL named interval color")


class QQPlotSpec(ChartSpec):
    """Normal Q-Q plot of a single continuous variable (via PPLOT)."""

    kind: Literal["qqplot"] = "qqplot"
    variable: str = Field(description="Continuous variable to assess")


class KMCurveSpec(ChartSpec):
    """Kaplan-Meier survival curve via the KM procedure."""

    kind: Literal["km_curve"] = "km_curve"
    time: str = Field(description="Survival time variable")
    status: str = Field(description="Event/censoring status variable")
    event: int = Field(
        default=1, description="Value of status that marks the event (default 1)"
    )
    group: Optional[str] = Field(
        default=None, description="Optional grouping variable for separate curves"
    )


class AreaSpec(ChartSpec):
    """Area chart of a continuous variable against a time/ordinal variable."""

    kind: Literal["area"] = "area"
    x: str = Field(description="X (typically time) variable")
    y: str = Field(description="Y variable")
    color: str = Field(default="steelblue", description="GPL named fill color")


class HistogramDensitySpec(ChartSpec):
    """Histogram overlaid with a normal density curve."""

    kind: Literal["histogram_density"] = "histogram_density"
    variable: str = Field(description="Continuous variable to bin")
    color: str = Field(default="darkgray", description="GPL named bar fill color")
    density_color: str = Field(
        default="red", description="GPL named density curve color"
    )


class BarErrorSpec(ChartSpec):
    """Bar chart of a category mean with confidence-interval error bars."""

    kind: Literal["bar_error"] = "bar_error"
    category: str = Field(description="Categorical variable for the X axis")
    value: str = Field(description="Continuous variable summarised per category")
    ci: float = Field(
        default=0.95, description="Confidence level, e.g. 0.95 for 95% CI"
    )
    color: str = Field(default="darkgray", description="GPL named fill color")


SPEC_BY_KIND: dict[str, type[ChartSpec]] = {
    "histogram": HistogramSpec,
    "scatter": ScatterSpec,
    "bar": BarSpec,
    "line": LineSpec,
    "boxplot": BoxplotSpec,
    "errorbar": ErrorbarSpec,
    "qqplot": QQPlotSpec,
    "km_curve": KMCurveSpec,
    "area": AreaSpec,
    "histogram_density": HistogramDensitySpec,
    "bar_error": BarErrorSpec,
}


def build_spec(kind: str, **kwargs) -> ChartSpec:
    """Instantiate the spec model matching ``kind``."""
    try:
        return SPEC_BY_KIND[kind](**kwargs)
    except KeyError:
        raise ValueError(f"Unsupported chart kind: {kind}") from None
