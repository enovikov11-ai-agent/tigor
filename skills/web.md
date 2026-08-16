# Single-File HTML Tools as Purpose-Built Alternatives to Big Software

Instead of learning DaVinci Resolve / Premiere / After Effects for a one-off video project, the pattern is: decompose the creative workflow into scriptable steps (ffmpeg, playwright, etc.) and build **minimal interactive HTML tools only for the parts that need human judgment** (choosing crop coordinates, marking timestamps, previewing overlays). The agent writes the tooling, the human makes creative decisions through simple single-purpose UIs.

Why this works:
* **Reproducible.** The whole pipeline is a README + scripts, not an opaque .prproj file. Re-running with different parameters is trivial.
* **No tool lock-in.** ffmpeg is universal; HTML runs everywhere. No licenses, no version hell, no project file migration.
* **AI-friendly iteration.** When the tool needs a tweak, the agent rewrites a single HTML file — no plugin API, no extension SDK. The feedback loop is: user describes what's wrong → agent rewrites → user reloads.
* **URL-as-state.** Querystring persistence means no backend, no save files — just bookmark or share the link. Good default for any throwaway planning tool.

Design rules for these tools:
* Start with the dumbest possible interaction. Click-drag-release to draw a rectangle beats resize handles, edge detection, hit testing, and drag state machines. If the first version has complex mouse interaction code, it's overengineered — nuke it and start simpler.
* One tool per decision. Don't build a "video editor" — build a "crop position picker" and a "timestamp marker". Composability > features.
* Output should be copy-pasteable CLI parameters (ffmpeg filters, coordinates), not internal state. The tool is a parameter picker for the scriptable pipeline.

This pattern generalizes beyond video: any domain where heavyweight GUI software exists but the actual task is narrow (image annotation, config visualization, data labeling, layout planning).

## Disposable Toolchains: Single-Use Jigs, Not Reusable Software

When the agent builds tools for a creative/media workflow (crop planner, timestamp marker, render script), these are **single-use jigs** — like in woodworking, you build a jig for one cut, use it, discard it. They don't need to be robust, maintainable, or general-purpose. They need to let the user make one decision, then get out of the way.

The economics: agent writes a tool nearly for free → user makes a creative decision through it → tool is discarded or rewritten from scratch for the next decision. Rewriting is cheaper than debugging or extending. This means:

* **Expect to throw away v1.** The first attempt will be wrong — either overengineered or misframed. That's fine. The rewrite costs one message. Don't invest in making v1 "complete."
* **The agent's instinct to add completeness is a trap.** Resize handles, edge detection, state management, undo — these feel like they make the tool "better" but they multiply interaction surface, introduce bugs, and waste a review cycle when the user says "nuke it." Build the literal dumbest thing that lets the user make the decision.
* **Optimize for "easy to throw away" not "robust."** No state management, no abstractions, no configuration layers. Hardcode everything. If requirements change, rewrite — don't refactor.
