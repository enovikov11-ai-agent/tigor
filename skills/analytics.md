# Jupyter Notebooks and Data Visualization

## Data correctness before visual polish

* Validate data with intermediate output cells and spot-checks before touching visuals. Don't iterate on presentation while the underlying numbers are wrong.
* When aggregating fine-grained data into buckets for display: compute at full resolution first, then aggregate. Never sample individual points to represent ranges.
* Spot-check results against intuition ("does a 20-year-old really have a 1/134 chance of dying at 20-24?"). If numbers feel off, stop polishing and debug the math.

## matplotlib pitfalls

* `SecondaryAxis` API varies across versions (e.g. no `set_ticklabels`). Use manual `ax.text()` for extra axis labels — it always works.
* For complex multi-panel layouts: render each panel as a separate figure, save to PNG, merge with PIL. Fighting matplotlib's axis/subplot system wastes iteration cycles.
* Start with the simplest visual (flat color, no legend, no fancy colormap) and add complexity only when asked. Over-engineering the first version means more throwaway work.
* For grid/table visualizations: add `savefig()` early and read the PNG before iterating on layout changes. Seeing the actual render catches issues faster than reasoning about coordinates.
* When a grid has two categories sharing a diagonal (e.g. male/female triangle layout), split diagonal cells horizontally (top/bottom halves) rather than diagonally — it's simpler to position text and keeps alignment clean.
* For grid visualizations with variable grid sizes: scale fig size and font sizes proportionally to the number of cells (`fig_size = max(base, n * factor)`, `font = min(cap, fig_size / (n + margin) * scale)`). Hardcoded font sizes break when the grid grows beyond the original design.

## Notebook structure for iteration

* Keep extraction, derivation, and rendering in separate cells. When iterating on visuals, only the last cell needs re-running.
* When derivation logic is wrong, stub it out with clear TODO + docstring of expected inputs/outputs/approach. Fresh session without accumulated confusion produces cleaner code.
* After editing a cell, verify it actually executed (check for output) before concluding the code is correct. VS Code notebook kernel can silently not run edited cells.

## External data sources

* Government/institutional websites often block automated access (curl, requests). User may need to save HTML manually. Store raw data files alongside notebook for reproducibility.
