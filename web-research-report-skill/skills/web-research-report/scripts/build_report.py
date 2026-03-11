#!/usr/bin/env python3
"""
Web Research Report - HTML builder.
Usage: python build_report.py --output report.html --title "..." --summary "..." \
       --findings '["..."]' --sections '[{"title":"...","content":"...","sources":[]}]' \
       --sources '[{"title":"...","url":"...","date":"..."}]'
"""
import argparse, json, base64, io
from pathlib import Path
from datetime import date

BG     = "#0f172a"
CARD   = "#1e293b"
ACCENT = "#6366f1"
AMBER  = "#f59e0b"
GREEN  = "#10b981"
TEXT   = "#f1f5f9"
MUTED  = "#94a3b8"
BORDER = "#334155"

ICONS  = ["🔍","📌","💡","⚡","🎯","📣","🔎","📊"]

def render(title, topic, summary, findings, sections, sources, output):
    # Findings
    findings_html = ""
    for i, f in enumerate(findings):
        icon = ICONS[i % len(ICONS)]
        findings_html += f"""
        <div class="finding">
          <span class="finding-icon">{icon}</span>
          <span>{f}</span>
        </div>"""

    # Sections
    sections_html = ""
    for sec in sections:
        src_links = ""
        for s in sec.get("sources", []):
            src_links += f'<a href="{s}" target="_blank" class="src-chip">{s[:50]}{"…" if len(s)>50 else ""}</a>'
        sections_html += f"""
        <div class="card section-card">
          <h3 class="section-title">{sec["title"]}</h3>
          <div class="section-body">{sec["content"].replace(chr(10), "<br>")}</div>
          {f'<div class="src-chips">{src_links}</div>' if src_links else ""}
        </div>"""

    # Sources
    sources_html = ""
    for i, s in enumerate(sources, 1):
        date_str = s.get("date", "")
        sources_html += f"""
        <div class="source-row">
          <span class="src-num">{i}</span>
          <div>
            <a href="{s.get('url','#')}" target="_blank" class="src-title">{s.get('title','Untitled')}</a>
            {f'<span class="src-date">{date_str}</span>' if date_str else ""}
          </div>
        </div>"""

    today = date.today().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  :root {{--bg:{BG};--card:{CARD};--accent:{ACCENT};--text:{TEXT};--muted:{MUTED};--border:{BORDER};}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;}}

  .header{{background:linear-gradient(135deg,#1e1b4b 0%,#312e81 40%,#4338ca 100%);padding:48px 40px 40px;position:relative;overflow:hidden;}}
  .header::before{{content:'';position:absolute;inset:0;opacity:.06;background:repeating-linear-gradient(45deg,#fff 0,#fff 1px,transparent 0,transparent 50%);background-size:20px 20px;}}
  .header-meta{{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:12px;position:relative;}}
  .header h1{{font-size:32px;font-weight:800;letter-spacing:-.5px;line-height:1.2;position:relative;max-width:800px;}}
  .header .topic{{color:rgba(255,255,255,.65);font-size:15px;margin-top:10px;position:relative;}}
  .header .date-badge{{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:20px;padding:4px 14px;font-size:12px;margin-top:16px;position:relative;}}

  .container{{max-width:1000px;margin:0 auto;padding:36px 24px;}}
  .section-label{{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin:40px 0 16px;}}

  .summary-card{{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--accent);border-radius:0 12px 12px 0;padding:20px 24px;font-size:15px;line-height:1.8;color:var(--text);margin-bottom:8px;}}

  .findings-grid{{display:flex;flex-direction:column;gap:10px;}}
  .finding{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 18px;display:flex;align-items:flex-start;gap:12px;font-size:14px;line-height:1.7;}}
  .finding-icon{{font-size:18px;flex-shrink:0;margin-top:1px;}}

  .card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:24px;margin-bottom:20px;}}
  .section-title{{font-size:17px;font-weight:700;color:var(--text);margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid var(--border);}}
  .section-body{{font-size:14px;line-height:1.9;color:#cbd5e1;}}
  .src-chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px;}}
  .src-chip{{font-size:11px;background:rgba(99,102,241,.15);color:{ACCENT};border:1px solid rgba(99,102,241,.3);border-radius:6px;padding:3px 10px;text-decoration:none;}}
  .src-chip:hover{{background:rgba(99,102,241,.25);}}

  .source-row{{display:flex;align-items:flex-start;gap:14px;padding:10px 0;border-bottom:1px solid #1e293b;}}
  .source-row:last-child{{border-bottom:none;}}
  .src-num{{min-width:24px;height:24px;background:rgba(99,102,241,.2);color:{ACCENT};border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;margin-top:1px;}}
  .src-title{{font-size:14px;color:{ACCENT};text-decoration:none;line-height:1.5;}}
  .src-title:hover{{text-decoration:underline;}}
  .src-date{{font-size:12px;color:var(--muted);margin-left:8px;}}

  .footer{{text-align:center;color:var(--muted);font-size:12px;padding:40px 0 24px;}}
</style>
</head>
<body>
<div class="header">
  <div class="header-meta">Research Report</div>
  <h1>{title}</h1>
  <div class="topic">{topic}</div>
  <div class="date-badge">📅 {today}</div>
</div>

<div class="container">
  <div class="section-label">Executive Summary</div>
  <div class="summary-card">{summary}</div>

  <div class="section-label">Key Findings</div>
  <div class="findings-grid">{findings_html if findings_html else '<div class="finding"><span class="finding-icon">📋</span><span>No findings provided.</span></div>'}</div>

  <div class="section-label">Research</div>
  {sections_html if sections_html else '<div class="card" style="color:var(--muted)">No sections provided.</div>'}

  {'<div class="section-label">Sources</div><div class="card">' + sources_html + '</div>' if sources_html else ''}
</div>

<div class="footer">Generated by Claude Cowork · web-research-report skill</div>
</body>
</html>"""

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report saved to: {output}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output",   required=True)
    p.add_argument("--title",    required=True)
    p.add_argument("--topic",    default="")
    p.add_argument("--summary",  default="")
    p.add_argument("--findings", default="[]")
    p.add_argument("--sections", default="[]")
    p.add_argument("--sources",  default="[]")
    args = p.parse_args()
    render(
        title=args.title, topic=args.topic, summary=args.summary,
        findings=json.loads(args.findings),
        sections=json.loads(args.sections),
        sources=json.loads(args.sources),
        output=args.output
    )

if __name__ == "__main__":
    main()
