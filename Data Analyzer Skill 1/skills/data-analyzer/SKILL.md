---
name: data-analyzer
description: >
  **Data Analyzer**: Load any CSV, Excel (.xlsx/.xls), or TSV file and produce
  a full analysis — summary statistics, trend detection, outlier flagging,
  correlation insights, and charts — delivered as a polished HTML report the
  user can open in their browser, plus an optional cleaned Excel output.

  ALWAYS use this skill when the user wants to: explore or understand a data
  file, find patterns or trends in rows/columns, generate charts or graphs from
  tabular data, get a summary of what's in a CSV or spreadsheet, check for
  anomalies or outliers, or produce any kind of data report. Trigger even if
  the user is vague (e.g. "what's in this file?", "analyze my sales data",
  "make sense of this spreadsheet").
---

# Data Analyzer Skill

Your job is to take a data file (CSV, Excel, or TSV) and produce a clear,
insightful analysis that actually helps the user understand their data — not
just print statistics, but tell a story about what the numbers mean.

## What you produce

1. **An HTML report** saved to the workspace folder — charts, tables, key
   findings, all in one file the user can open in any browser.
2. **Optionally a cleaned Excel file** — if the data had issues (missing
   values, weird formatting, duplicates), output a cleaned version too.

---

## Step-by-step process

### 1. Load and inspect the file

Use the `analyze.py` script in `scripts/` to do the heavy lifting:

```bash
python /path/to/data-analyzer/scripts/analyze.py \
  --input "/path/to/datafile.csv" \
  --output "/path/to/output/report.html"
```

If the script fails or the file needs special handling (multi-sheet Excel,
unusual encoding, malformed CSV), handle it inline with Python — install
packages as needed with `pip install pandas openpyxl matplotlib seaborn --break-system-packages`.

### 2. Understand the data before writing anything

Before generating output, read the script results and reason through:
- What is this data actually about? What does each column represent?
- What time range, geography, or entity does it cover?
- What are the most interesting/surprising things in it?
- What questions would a curious person naturally ask about this dataset?

This thinking shapes the narrative in your report. Don't skip it.

### 3. Write the HTML report

Use the template in `references/report_template.html` as a starting point.
The report must include:

**Header section**
- Dataset name, row/column count, date range if applicable
- One-paragraph plain-English summary: what this data is, what it covers,
  and the 2-3 most notable things you found

**Key findings** (3–5 bullet points, each with a number)
- Lead with the most surprising or actionable insight
- Quantify everything: "Revenue grew 34% between Jan and Jun" not "Revenue grew"

**Charts** (embed as base64 PNG inside the HTML so it's self-contained)
- Always include at least 2 charts
- Choose chart types based on the data: time series → line chart, categories
  → bar chart, relationships → scatter, distributions → histogram
- Label axes clearly, include titles, use readable font sizes

**Data quality section**
- Missing value counts per column
- Duplicate rows if any
- Any columns that looked suspicious or had inconsistent formats

**Full summary statistics table**
- Mean, median, min, max, std for numeric columns
- Value counts for categorical columns with ≤20 unique values

### 4. Save and share

Save the report to the user's workspace folder. Then share it with them:
```
[View your analysis report](computer:///path/to/report.html)
```

Give a 2-sentence summary of the top finding before the link. Don't over-explain —
the report has all the detail they need.

---

## Handling edge cases

**Large files (>100k rows):** Sample 50k rows for charts/correlations, but
report full statistics. Tell the user you sampled.

**Mostly text data:** Focus on value counts, word frequency if applicable,
and flag any numeric columns you did find.

**Multiple Excel sheets:** Analyze each sheet separately, combine into one
report with a tab or section per sheet.

**Completely empty / unreadable file:** Tell the user clearly what went wrong
and what format you'd need instead.

---

## What makes a good report vs. a bad one

Good:
- "Sales peaked in Q3 at $1.2M, driven by the Western region (+67% YoY)"
- "18% of rows have missing values in the `email` column — this will affect
  any analysis that relies on customer contact data"
- Charts with labeled axes, clear titles, readable text

Bad:
- Dumping raw `df.describe()` output without interpretation
- Generic statements like "the data has some variation"
- Tiny unreadable chart labels
- HTML that requires external CDN links (embed everything)
