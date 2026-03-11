#!/usr/bin/env python3
"""
Data Analyzer - Core analysis script.
Usage: python analyze.py --input <file> --output <report.html>
"""

import argparse
import base64
import io
import json
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

try:
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import seaborn as sns
except ImportError:
    print("Installing required packages...")
    os.system("pip install pandas openpyxl matplotlib seaborn numpy --break-system-packages -q")
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import seaborn as sns

# ── Palette ──────────────────────────────────────────────────────────────────
PALETTE = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#3b82f6", "#8b5cf6"]
BG      = "#0f172a"   # dark navy
CARD    = "#1e293b"   # slightly lighter card bg
TEXT    = "#f1f5f9"
MUTED   = "#94a3b8"
ACCENT  = "#6366f1"   # indigo

plt.rcParams.update({
    "figure.facecolor":  CARD,
    "axes.facecolor":    CARD,
    "axes.edgecolor":    "#334155",
    "axes.labelcolor":   TEXT,
    "axes.titlecolor":   TEXT,
    "axes.titlesize":    13,
    "axes.titleweight":  "bold",
    "axes.titlepad":     12,
    "xtick.color":       MUTED,
    "ytick.color":       MUTED,
    "grid.color":        "#1e3a5f",
    "grid.linewidth":    0.5,
    "text.color":        TEXT,
    "font.size":         11,
    "font.family":       "sans-serif",
})


def load_file(path: str) -> pd.DataFrame:
    p = Path(path)
    ext = p.suffix.lower()
    if ext in (".xlsx", ".xls", ".xlsm"):
        return pd.read_excel(path)
    elif ext == ".tsv":
        return pd.read_csv(path, sep="\t")
    else:
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                return pd.read_csv(path, encoding=enc)
            except Exception:
                continue
        raise ValueError(f"Could not read file: {path}")


def fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


def make_charts(df: pd.DataFrame) -> list[dict]:
    charts = []
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    date_cols = [c for c in df.columns if any(k in c.lower() for k in ("date","time","year","month","day"))]

    # ── Chart 1: Histogram ───────────────────────────────────────────────────
    if numeric_cols:
        col = numeric_cols[0]
        fig, ax = plt.subplots(figsize=(7, 4), facecolor=CARD)
        data = df[col].dropna()
        n, bins, patches = ax.hist(data, bins=min(30, max(10, len(data)//20)),
                                   edgecolor="none", alpha=0.9)
        # gradient color by bin
        for i, patch in enumerate(patches):
            patch.set_facecolor(plt.cm.plasma(i / len(patches)))
        ax.set_title(f"Distribution · {col}")
        ax.set_xlabel(col, color=MUTED)
        ax.set_ylabel("Count", color=MUTED)
        ax.spines[["top","right","left","bottom"]].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", alpha=0.3)
        fig.tight_layout()
        charts.append({"title": f"Distribution: {col}", "b64": fig_to_b64(fig)})

    # ── Chart 2: Time series ─────────────────────────────────────────────────
    date_col = None
    for dc in date_cols:
        try:
            df[dc] = pd.to_datetime(df[dc], infer_datetime_format=True, errors="coerce")
            if df[dc].notna().sum() > 5:
                date_col = dc
                break
        except Exception:
            pass

    if date_col and numeric_cols:
        col = numeric_cols[0]
        ts = df[[date_col, col]].dropna().sort_values(date_col)
        if len(ts) > 1:
            fig, ax = plt.subplots(figsize=(8, 4), facecolor=CARD)
            ax.fill_between(ts[date_col], ts[col], alpha=0.18, color=ACCENT)
            ax.plot(ts[date_col], ts[col], color=ACCENT, linewidth=2)
            # highlight max point
            idx_max = ts[col].idxmax()
            ax.scatter([ts.loc[idx_max, date_col]], [ts.loc[idx_max, col]],
                       color="#f59e0b", s=80, zorder=5)
            ax.set_title(f"{col} over time")
            ax.set_xlabel(date_col, color=MUTED)
            ax.set_ylabel(col, color=MUTED)
            ax.spines[["top","right","left","bottom"]].set_visible(False)
            ax.yaxis.grid(True, linestyle="--", alpha=0.3)
            plt.xticks(rotation=30, ha="right")
            fig.tight_layout()
            charts.append({"title": f"{col} over time", "b64": fig_to_b64(fig)})

    # ── Chart 3: Horizontal bar chart for top categorical ───────────────────
    cat_cols = df.select_dtypes(include=["object","category"]).columns.tolist()
    if cat_cols:
        col = cat_cols[0]
        vc = df[col].value_counts().head(12)
        if len(vc) >= 2:
            fig, ax = plt.subplots(figsize=(7, max(3, len(vc) * 0.45)), facecolor=CARD)
            bars = ax.barh(vc.index[::-1], vc.values[::-1],
                           color=[PALETTE[i % len(PALETTE)] for i in range(len(vc))],
                           edgecolor="none", height=0.65)
            # value labels
            for bar, val in zip(bars, vc.values[::-1]):
                ax.text(bar.get_width() + max(vc.values)*0.01, bar.get_y() + bar.get_height()/2,
                        f"{val:,}", va="center", color=TEXT, fontsize=10)
            ax.set_title(f"Top values · {col}")
            ax.set_xlabel("Count", color=MUTED)
            ax.spines[["top","right","left","bottom"]].set_visible(False)
            ax.xaxis.grid(True, linestyle="--", alpha=0.3)
            ax.set_xlim(0, max(vc.values) * 1.18)
            fig.tight_layout()
            charts.append({"title": f"Top values: {col}", "b64": fig_to_b64(fig)})

    # ── Chart 4: Correlation heatmap or scatter ──────────────────────────────
    if len(numeric_cols) >= 4:
        corr = df[numeric_cols[:8]].corr()
        fig, ax = plt.subplots(figsize=(7, 6), facecolor=CARD)
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
                    square=True, linewidths=0.5, linecolor="#0f172a",
                    annot_kws={"size": 10, "color": TEXT},
                    ax=ax, mask=mask,
                    cbar_kws={"shrink": 0.75})
        ax.set_title("Correlation Matrix")
        ax.tick_params(colors=MUTED)
        plt.xticks(rotation=35, ha="right")
        fig.tight_layout()
        charts.append({"title": "Correlation Matrix", "b64": fig_to_b64(fig)})
    elif len(numeric_cols) == 2:
        fig, ax = plt.subplots(figsize=(6, 5), facecolor=CARD)
        ax.scatter(df[numeric_cols[0]], df[numeric_cols[1]],
                   alpha=0.55, color="#f59e0b", s=25, edgecolors="none")
        ax.set_xlabel(numeric_cols[0], color=MUTED)
        ax.set_ylabel(numeric_cols[1], color=MUTED)
        ax.set_title(f"{numeric_cols[0]} vs {numeric_cols[1]}")
        ax.spines[["top","right","left","bottom"]].set_visible(False)
        ax.grid(True, linestyle="--", alpha=0.3)
        fig.tight_layout()
        charts.append({"title": f"Scatter: {numeric_cols[0]} vs {numeric_cols[1]}", "b64": fig_to_b64(fig)})

    return charts


def compute_stats(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object","category"]).columns.tolist()

    numeric_stats = {}
    for col in numeric_cols:
        s = df[col].dropna()
        numeric_stats[col] = {
            "count": int(s.count()),
            "mean": round(float(s.mean()), 2) if len(s) else None,
            "median": round(float(s.median()), 2) if len(s) else None,
            "std": round(float(s.std()), 2) if len(s) else None,
            "min": round(float(s.min()), 2) if len(s) else None,
            "max": round(float(s.max()), 2) if len(s) else None,
            "missing": int(df[col].isna().sum()),
        }

    cat_stats = {}
    for col in cat_cols:
        vc = df[col].value_counts()
        cat_stats[col] = {
            "unique": int(df[col].nunique()),
            "top_values": vc.head(10).to_dict(),
            "missing": int(df[col].isna().sum()),
        }

    return {"numeric": numeric_stats, "categorical": cat_stats}


def fmt_num(n):
    """Format number nicely: 1234567 → 1.23M, 12345 → 12.3K"""
    if n is None: return "—"
    if abs(n) >= 1_000_000: return f"{n/1_000_000:.2f}M"
    if abs(n) >= 1_000: return f"{n/1_000:.1f}K"
    return f"{n:,.2f}" if isinstance(n, float) else f"{n:,}"


def render_html(df: pd.DataFrame, charts: list, stats: dict,
                filename: str, findings: list[str]) -> str:
    rows, cols_count = df.shape
    missing_total = int(df.isna().sum().sum())
    dupe_count = int(df.duplicated().sum())
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    # ── KPI cards ────────────────────────────────────────────────────────────
    kpi_cards = ""
    kpi_items = [
        ("📋", "Rows", f"{rows:,}"),
        ("🔢", "Columns", str(cols_count)),
        ("⚠️", "Missing", f"{missing_total:,}"),
        ("🔄", "Duplicates", str(dupe_count)),
    ]
    if numeric_cols:
        col = numeric_cols[0]
        s = df[col].dropna()
        kpi_items += [
            ("📈", f"Max {col}", fmt_num(float(s.max()))),
            ("📊", f"Avg {col}", fmt_num(float(s.mean()))),
        ]
    for icon, label, val in kpi_items:
        kpi_cards += f"""
        <div class="kpi">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-val">{val}</div>
          <div class="kpi-label">{label}</div>
        </div>"""

    # ── Charts ───────────────────────────────────────────────────────────────
    charts_html = ""
    for i in range(0, len(charts), 2):
        charts_html += '<div class="chart-row">'
        for chart in charts[i:i+2]:
            charts_html += f"""
            <div class="card chart-card">
              <div class="card-title">{chart["title"]}</div>
              <img src="data:image/png;base64,{chart["b64"]}" class="chart-img"/>
            </div>"""
        charts_html += "</div>"

    # ── Findings ─────────────────────────────────────────────────────────────
    icons = ["🔍","📌","💡","⚡","🎯","📣"]
    findings_html = ""
    for i, f in enumerate(findings):
        findings_html += f"""
        <div class="finding">
          <span class="finding-icon">{icons[i % len(icons)]}</span>
          <span>{f}</span>
        </div>"""

    # ── Numeric stats table ──────────────────────────────────────────────────
    num_table = ""
    if stats["numeric"]:
        rows_html = ""
        for col, s in stats["numeric"].items():
            miss_color = "#ef4444" if s["missing"] > 0 else "#10b981"
            rows_html += f"""<tr>
              <td class="col-name">{col}</td>
              <td>{s['count']:,}</td>
              <td>{fmt_num(s['mean'])}</td>
              <td>{fmt_num(s['median'])}</td>
              <td>{fmt_num(s['std'])}</td>
              <td>{fmt_num(s['min'])}</td>
              <td>{fmt_num(s['max'])}</td>
              <td style="color:{miss_color};font-weight:600">{s['missing']}</td>
            </tr>"""
        num_table = f"""
        <div class="card" style="margin-bottom:24px">
          <div class="card-title">Numeric Statistics</div>
          <div style="overflow-x:auto">
          <table class="stats-table">
            <thead><tr>
              <th>Column</th><th>Count</th><th>Mean</th><th>Median</th>
              <th>Std Dev</th><th>Min</th><th>Max</th><th>Missing</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
          </div>
        </div>"""

    # ── Categorical progress bars ─────────────────────────────────────────────
    cat_html = ""
    for ci, (col, cs) in enumerate(stats["categorical"].items()):
        if cs["unique"] <= 20:
            top = list(cs["top_values"].items())[:8]
            total = sum(cs["top_values"].values())
            bars = ""
            for vi, (k, v) in enumerate(top):
                pct = round(100 * v / total, 1)
                color = PALETTE[vi % len(PALETTE)]
                bars += f"""
                <div class="cat-row">
                  <div class="cat-label">{k}</div>
                  <div class="cat-bar-wrap">
                    <div class="cat-bar" style="width:{pct}%;background:{color}"></div>
                  </div>
                  <div class="cat-val">{v:,} <span class="cat-pct">({pct}%)</span></div>
                </div>"""
            cat_html += f"""
            <div class="card" style="margin-bottom:20px">
              <div class="card-title">{col} <span class="badge">{cs['unique']} unique</span></div>
              {bars}
            </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Analysis · {filename}</title>
<style>
  :root {{
    --bg: {BG};
    --card: {CARD};
    --accent: {ACCENT};
    --text: {TEXT};
    --muted: {MUTED};
    --border: #334155;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }}

  /* ── Header ── */
  .header {{
    background: linear-gradient(135deg, #312e81 0%, #4f46e5 50%, #7c3aed 100%);
    padding: 36px 40px 32px;
    position: relative;
    overflow: hidden;
  }}
  .header::before {{
    content: '';
    position: absolute; inset: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  }}
  .header h1 {{ font-size: 28px; font-weight: 700; letter-spacing: -0.5px; position: relative; }}
  .header .subtitle {{ color: rgba(255,255,255,0.7); font-size: 14px; margin-top: 6px; position: relative; }}
  .header .file-tag {{
    display: inline-block; background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px; padding: 4px 14px; font-size: 13px;
    margin-top: 12px; position: relative;
  }}

  /* ── Layout ── */
  .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
  .section-title {{
    font-size: 13px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--muted);
    margin: 36px 0 16px;
  }}

  /* ── KPI cards ── */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 16px;
    margin-bottom: 8px;
  }}
  .kpi {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 18px;
    text-align: center;
    transition: transform .15s;
  }}
  .kpi:hover {{ transform: translateY(-2px); }}
  .kpi-icon {{ font-size: 22px; margin-bottom: 8px; }}
  .kpi-val {{ font-size: 26px; font-weight: 700; color: var(--text); }}
  .kpi-label {{ font-size: 12px; color: var(--muted); margin-top: 4px; text-transform: uppercase; letter-spacing: .8px; }}

  /* ── Findings ── */
  .findings-grid {{ display: flex; flex-direction: column; gap: 10px; }}
  .finding {{
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    display: flex; align-items: flex-start; gap: 12px;
    font-size: 14px; line-height: 1.6;
  }}
  .finding-icon {{ font-size: 18px; flex-shrink: 0; margin-top: 1px; }}

  /* ── Cards ── */
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }}
  .card-title {{
    font-size: 13px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; color: var(--muted); margin-bottom: 16px;
  }}

  /* ── Charts ── */
  .chart-row {{ display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }}
  .chart-card {{ flex: 1; min-width: 300px; }}
  .chart-img {{ width: 100%; border-radius: 6px; display: block; }}

  /* ── Stats table ── */
  .stats-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .stats-table thead tr {{ background: rgba(99,102,241,0.15); }}
  .stats-table th {{
    padding: 10px 12px; text-align: center;
    color: var(--muted); font-weight: 600; font-size: 11px;
    letter-spacing: .8px; text-transform: uppercase;
    border-bottom: 1px solid var(--border);
  }}
  .stats-table th:first-child {{ text-align: left; }}
  .stats-table td {{ padding: 9px 12px; text-align: center; border-bottom: 1px solid #1e293b; }}
  .stats-table td:first-child {{ text-align: left; }}
  .stats-table tbody tr:hover {{ background: rgba(255,255,255,.03); }}
  .col-name {{ font-weight: 600; color: var(--accent); }}

  /* ── Categorical bars ── */
  .cat-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 8px; font-size: 13px; }}
  .cat-label {{ width: 110px; flex-shrink: 0; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .cat-bar-wrap {{ flex: 1; background: #1e3a5f; border-radius: 4px; height: 8px; overflow: hidden; }}
  .cat-bar {{ height: 100%; border-radius: 4px; transition: width .4s; }}
  .cat-val {{ width: 80px; text-align: right; color: var(--text); font-weight: 600; flex-shrink: 0; }}
  .cat-pct {{ color: var(--muted); font-weight: 400; font-size: 11px; }}
  .badge {{
    background: rgba(99,102,241,0.2); color: var(--accent);
    border-radius: 12px; padding: 2px 10px; font-size: 11px;
    font-weight: 600; margin-left: 8px; vertical-align: middle;
    letter-spacing: 0;
  }}

  /* ── Footer ── */
  .footer {{ text-align: center; color: var(--muted); font-size: 12px; padding: 40px 0 24px; }}
</style>
</head>
<body>

<div class="header">
  <h1>📊 Data Analysis Report</h1>
  <div class="subtitle">Automated insights generated by Claude Cowork</div>
  <div class="file-tag">📁 {filename}</div>
</div>

<div class="container">

  <div class="section-title">Overview</div>
  <div class="kpi-grid">{kpi_cards}</div>

  <div class="section-title">Key Findings</div>
  <div class="findings-grid">{findings_html if findings_html else '<div class="finding"><span class="finding-icon">📋</span><span>No findings provided.</span></div>'}</div>

  <div class="section-title">Charts</div>
  {charts_html if charts_html else '<div class="card" style="color:var(--muted)">No charts could be generated.</div>'}

  <div class="section-title">Statistics</div>
  {num_table}

  <div class="section-title">Categorical Breakdown</div>
  {cat_html if cat_html else '<div class="card" style="color:var(--muted)">No categorical columns with ≤20 unique values.</div>'}

</div>

<div class="footer">Generated by Claude Cowork · data-analyzer skill</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--findings", default="[]")
    args = parser.parse_args()

    df = load_file(args.input)
    charts = make_charts(df)
    stats = compute_stats(df)

    try:
        findings = json.loads(args.findings)
    except Exception:
        findings = []

    html = render_html(df, charts, stats, Path(args.input).name, findings)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(json.dumps({
        "rows": len(df), "cols": len(df.columns),
        "columns": df.columns.tolist(),
        "numeric_cols": df.select_dtypes(include="number").columns.tolist(),
        "missing_total": int(df.isna().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
        "stats": stats,
    }, indent=2))


if __name__ == "__main__":
    main()
