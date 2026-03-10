# Phase 7: Dashboard and README - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can view benchmark trends over time on a public GitHub Pages dashboard and see live figures in the README. Static PNG references in the README are replaced with a dashboard link. Data growth on gh-pages is limited via max-items-in-chart.

</domain>

<decisions>
## Implementation Decisions

### Dashboard page content
- Custom wrapper index.html at gh-pages root with project name, one-line description, install command, and links (repo, PyPI, benchmark charts at /dev/bench/)
- Minimal content — fits in a single screen, just links and a tagline
- Links to /dev/bench/ for charts (no iframe embedding)
- Commit index.html once to gh-pages manually — github-action-benchmark only writes to /dev/bench/ so root is untouched by CI

### README benchmark figures
- Replace all static PNG references in README Benchmarks section with a "View benchmark dashboard" link to GitHub Pages
- Keep summary text describing what's benchmarked (backends, operations, dataset matrix)
- Dashboard link only — no mention of PR comparison feature in README
- Keep docs/benchmark_*.png files and docs/visualize_benchmarks.py in the repo (used for publication/local exploration) — just remove PNG image references from README

### Data growth limits
- max-items-in-chart: 200 (covers ~6 months of history at daily pushes)
- Apply only to the main (store) step — PR comparison step doesn't write data so the setting is a no-op there

### Claude's Discretion
- Exact HTML/CSS styling for the landing page
- How to structure the dashboard link in README (badge vs plain link vs button-style)
- Whether to add a brief "Contributing" note about benchmark checks on PRs

</decisions>

<specifics>
## Specific Ideas

- User wants docs/benchmark_*.png and visualize_benchmarks.py kept for potential publication use — these are not deleted, just dereferenced from README
- Landing page should be minimal — not a condensed README, just the essentials to orient visitors

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.github/workflows/benchmark.yml` — existing workflow with main (store) and PR (compare) steps; max-items-in-chart needs to be added to the main step
- gh-pages branch at `dev/bench/` — auto-generated Chart.js dashboard already served by GitHub Pages

### Established Patterns
- `benchmark-action/github-action-benchmark@v1` with `tool: "pytest"`, `gh-pages-branch: gh-pages`, `benchmark-data-dir-path: dev/bench`
- GITHUB_TOKEN for gh-pages pushes (no deploy key)

### Integration Points
- `.github/workflows/benchmark.yml` — add `max-items-in-chart: 200` to the main store step
- `README.md` — replace Benchmarks section PNG references with dashboard link
- gh-pages branch root — commit new index.html (one-time, outside normal CI flow)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-dashboard-and-readme*
*Context gathered: 2026-03-10*
