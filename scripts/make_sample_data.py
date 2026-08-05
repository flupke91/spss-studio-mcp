"""Generate the four sample datasets used for the P1 chart archive.

Produces .sav files under ``examples/data`` (survey / experiment / survival /
mediation scenarios) with Chinese variable and value labels, so the SPSS
engine can load them via GET FILE and chart tools can export real figures.

Usage:
    python scripts/make_sample_data.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
DATA_DIR = EXAMPLES / "data"

RNG = np.random.default_rng(20260804)


def _clip_round(x: np.ndarray, lo: int, hi: int) -> np.ndarray:
    return np.clip(np.round(x), lo, hi).astype(int)


def make_survey() -> pd.DataFrame:
    """Survey scenario: 200 students, learning-engagement Likert items."""
    n = 200
    # Three engagement facets (4 items each, 1-5 Likert).
    cognitive = _clip_round(RNG.normal(3.2, 0.9, (n, 4)), 1, 5)
    affective = _clip_round(RNG.normal(3.6, 0.8, (n, 4)), 1, 5)
    behavioral = _clip_round(RNG.normal(3.0, 1.0, (n, 4)), 1, 5)
    items = np.hstack([cognitive, affective, behavioral])
    # Reverse-scored items: q4 and q8.
    items[:, 3] = 6 - items[:, 3]
    items[:, 7] = 6 - items[:, 7]
    df = pd.DataFrame(
        {
            "gender": RNG.choice([1, 2], n, p=[0.55, 0.45]),
            "major": RNG.choice([1, 2, 3], n, p=[0.4, 0.35, 0.25]),
            **{f"q{i + 1}": items[:, i] for i in range(12)},
        }
    )
    df["cognitive"] = items[:, :4].sum(axis=1)
    df["affective"] = items[:, 4:8].sum(axis=1)
    df["behavioral"] = items[:, 8:].sum(axis=1)
    df["engagement_total"] = df["cognitive"] + df["affective"] + df["behavioral"]
    labels = {
        "gender": {1: "男", 2: "女"},
        "major": {1: "文科", 2: "理科", 3: "工科"},
    }
    var_labels = {
        "gender": "性别",
        "major": "专业",
        "cognitive": "认知投入",
        "affective": "情感投入",
        "behavioral": "行为投入",
        "engagement_total": "学习投入总分",
        **{f"q{i + 1}": f"学习投入题项 {i + 1}" for i in range(12)},
    }
    return df, labels, var_labels


def make_experiment() -> pd.DataFrame:
    """Experiment scenario: 120 subjects, memory-training pretest/posttest."""
    n = 120
    group = RNG.choice([1, 2], n)
    pretest = _clip_round(RNG.normal(60, 12, n), 0, 100)
    # Training group gains ~+15, control ~+4.
    gain = RNG.normal(15, 6, n) * (group == 1) + RNG.normal(4, 5, n) * (group == 2)
    posttest = np.clip(pretest + gain, 0, 100)
    df = pd.DataFrame(
        {
            "group": group,
            "pretest": pretest,
            "posttest": np.round(posttest).astype(int),
        }
    )
    df["gain"] = df["posttest"] - df["pretest"]
    labels = {"group": {1: "训练组", 2: "对照组"}}
    var_labels = {
        "group": "实验分组",
        "pretest": "前测成绩",
        "posttest": "后测成绩",
        "gain": "前后测增益",
    }
    return df, labels, var_labels


def make_survival() -> pd.DataFrame:
    """Survival scenario: 150 patients, follow-up months with censoring."""
    n = 150
    treatment = RNG.choice([1, 2], n, p=[0.5, 0.5])
    # New drug (1): median ~22 months; standard (2): median ~12 months.
    rate = np.where(treatment == 1, 1 / 22, 1 / 12)
    time = RNG.exponential(scale=1 / rate, size=n)
    # Censor ~25% at a cut-off to mimic study termination.
    censored = RNG.random(n) < 0.25
    time = np.minimum(time, 36.0)
    status = np.where(censored, 0, 1).astype(int)
    df = pd.DataFrame(
        {
            "treatment": treatment,
            "time": np.round(time, 1),
            "status": status,
        }
    )
    labels = {
        "treatment": {1: "新药组", 2: "标准治疗组"},
        "status": {0: "删失", 1: "死亡"},
    }
    var_labels = {
        "treatment": "治疗方案",
        "time": "随访月数",
        "status": "结局状态",
    }
    return df, labels, var_labels


def make_longitudinal() -> pd.DataFrame:
    """Longitudinal scenario: 60 subjects, three repeated measures."""
    n = 60
    group = RNG.choice([1, 2], n)
    base = RNG.normal(50, 8, n)
    growth = RNG.normal(0.5, 1.5, n) + 4.0 * (group == 1)
    t1 = _clip_round(base + RNG.normal(0, 3, n), 0, 100)
    t2 = _clip_round(base + growth + RNG.normal(0, 3, n), 0, 100)
    t3 = _clip_round(base + 2 * growth + RNG.normal(0, 3, n), 0, 100)
    df = pd.DataFrame(
        {
            "id": np.arange(1, n + 1),
            "group": group,
            "time1": t1,
            "time2": t2,
            "time3": t3,
        }
    )
    labels = {"group": {1: "训练组", 2: "对照组"}}
    var_labels = {
        "id": "被试编号",
        "group": "分组",
        "time1": "第 1 次测量",
        "time2": "第 2 次测量",
        "time3": "第 3 次测量",
    }
    return df, labels, var_labels


def make_longitudinal_long() -> pd.DataFrame:
    """Long-format longitudinal data (id x time) for MIXED/GENLINMIXED."""
    df, labels, var_labels = make_longitudinal()
    melted = pd.DataFrame(
        {
            "id": np.repeat(df["id"], 3),
            "group": np.repeat(df["group"], 3),
            "time": np.tile([1, 2, 3], len(df)),
            "score": np.concatenate([df["time1"], df["time2"], df["time3"]]),
        }
    )
    long_labels = {
        "group": labels["group"],
        "time": {1: "第 1 次", 2: "第 2 次", 3: "第 3 次"},
    }
    long_var_labels = {
        "id": "被试编号",
        "group": "分组",
        "time": "测量时间点",
        "score": "测量得分",
    }
    measures = {"id": "nominal", "group": "nominal", "time": "nominal"}
    return melted, long_labels, long_var_labels, measures


def make_mediation() -> pd.DataFrame:
    """Mediation scenario: 300 employees, autonomy -> satisfaction -> performance."""
    n = 300
    autonomy = _clip_round(RNG.normal(4.5, 1.2, n), 1, 7)
    # satisfaction is partly explained by autonomy, plus noise.
    satisfaction = _clip_round(0.55 * autonomy + RNG.normal(2.0, 0.9, n), 1, 7)
    # performance explained by autonomy (direct) + satisfaction (indirect).
    performance = _clip_round(
        0.35 * autonomy + 0.45 * satisfaction + RNG.normal(1.2, 0.8, n), 1, 7
    )
    df = pd.DataFrame(
        {
            "autonomy": autonomy,
            "satisfaction": satisfaction,
            "performance": performance,
        }
    )
    var_labels = {
        "autonomy": "工作自主性",
        "satisfaction": "工作满意度",
        "performance": "工作绩效",
    }
    return df, None, var_labels


def _write(name: str, df: pd.DataFrame, labels, var_labels, measures=None) -> Path:
    out = DATA_DIR / name
    pyreadstat.write_sav(
        df,
        out,
        variable_value_labels=labels or {},
        column_labels=var_labels,
        variable_measure=measures or {},
    )
    return out


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, maker, desc in [
        ("survey_study.sav", make_survey, "问卷"),
        ("experiment_study.sav", make_experiment, "实验"),
        ("survival_study.sav", make_survival, "生存"),
        ("mediation_study.sav", make_mediation, "中介"),
        ("longitudinal_study.sav", make_longitudinal, "纵向"),
        ("long_study.sav", make_longitudinal_long, "纵向长格式"),
    ]:
        df, labels, var_labels, measures = (
            maker() if len(maker()) == 4 else (*maker(), None)
        )
        out = _write(name, df, labels, var_labels, measures)
        # Round-trip check so SPSS can definitely read the file.
        read, _ = pyreadstat.read_sav(out)
        assert list(read.columns) == list(df.columns), name
        print(
            f"wrote {desc}: {out.name} ({out.stat().st_size} bytes, "
            f"{len(df)} rows x {len(df.columns)} cols)"
        )


if __name__ == "__main__":
    main()
