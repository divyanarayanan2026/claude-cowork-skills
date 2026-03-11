---
name: web-research-report
description: >
  **Web Research Report**: Search the web on any topic and produce a
  polished, well-sourced HTML report with an executive summary, key findings,
  sections with evidence, and a source list — all saved as a single
  self-contained file the user can share or keep.

  ALWAYS use this skill when the user asks to: research a topic and produce a
  report or document, find out what's happening with something and write it up,
  investigate a company/product/trend/person and summarise findings, gather
  information from multiple sources into one place, or produce a "briefing",
  "overview", "deep dive", or "research" on any subject. Trigger even for
  casual requests like "find out about X" or "what's the deal with Y" when a
  written output is expected. Also trigger when the user says things like
  "make me a report", "write me a summary of the research", or "I need a
  document on this topic".
---

# Web Research Report Skill

Your job is to research a topic thoroughly using web search, then write a
clear, well-structured HTML report that gives the user real insight — not
just a list of links, but an actual synthesis of what you found.

## What you produce

A **self-contained HTML report** saved to the workspace folder. One file,
opens in any browser, ready to share. No external dependencies.

---

## Step-by-step process

### 1. Clarify the scope (if needed)

If the request is vague, make a reasonable assumption and state it upfront
rather than asking multiple questions. One clarifying question is fine if
the topic is genuinely ambiguous (e.g. "Apple — the company or the fruit?").

### 2. Research — search in rounds

Don't do one search and call it done. Research in at least 2–3 rounds:

- **Round 1**: Broad overview — get the landscape, main players, key facts
- **Round 2**: Dig into the most interesting threads from round 1
- **Round 3**: Fill gaps, find recent data, look for counterpoints or caveats

Use `WebSearch` and `WebFetch` to gather from multiple sources. Aim for
at least 5–8 distinct sources. Prioritise:
- Recent sources (last 12 months where relevant)
- Primary sources over aggregators
- Specific data points and numbers over vague claims

### 3. Synthesise — don't just summarise

Before writing, ask yourself:
- What are the 3–5 most important things to understand about this topic?
- What would surprise an intelligent person who knew nothing about it?
- What's contested or uncertain?
- What are the practical implications?

These questions shape your Key Findings section.

### 4. Write the report using the template

Use `scripts/build_report.py` to generate the HTML:

```bash
python /path/to/web-research-report/scripts/build_report.py \
  --output "/path/to/output/report.html" \
  --title "Your Report Title" \
  --topic "The topic in one sentence" \
  --summary "2-3 sentence executive summary" \
  --findings '["Finding 1 with a specific number or fact", "Finding 2", ...]' \
  --sections '[{"title": "Section Title", "content": "Section body text...", "sources": ["url1", "url2"]}]' \
  --sources '[{"title": "Source Name", "url": "https://...", "date": "2025"}]'
```

If the script isn't available or the topic needs special structure, build
the HTML directly in Python — follow the visual style described in
`references/report_style.md`.

### 5. Save and share

Save to the workspace folder. Share with:
```
[View your research report](computer:///path/to/report.html)
```

Lead with 1–2 sentences on the most surprising finding before the link.

---

## Quality bar

A good report:
- Has a punchy executive summary that stands alone (someone should be able
  to read just that and understand the topic)
- Leads Key Findings with the most surprising or counterintuitive insight
- Backs every claim with a source — no floating assertions
- Uses specific numbers and dates, not vague language
- Acknowledges what is uncertain or contested
- Is scannable: headers, short paragraphs, findings as distinct callouts

A bad report:
- Paraphrases Wikipedia without adding synthesis
- Lists sources without connecting them into an argument
- Uses phrases like "experts say" or "it is widely believed" without citing anyone
- Ignores the most recent developments on a fast-moving topic

---

## Edge cases

**Topic too broad** (e.g. "AI"): Narrow to the most useful angle for the
user. State what angle you chose and why.

**Topic too narrow / little info available**: Say so clearly. Report what
you found, note the gaps, suggest related angles that had more coverage.

**Controversial topic**: Present multiple perspectives fairly. Don't editorialize.
Note where experts disagree.

**Time-sensitive topic**: Always check for the most recent information.
Flag if your sources are older than 6 months on a fast-moving subject.
