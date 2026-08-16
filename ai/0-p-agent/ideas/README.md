- Opencode integration
- OpenHands agent
- Harden openwebui


# Orchestration

## MVP

1. Supervisor watches repo goals:
   AGENTS.md
   TODO.md
   issues/
   failing tests
   lint warnings
   benchmark regressions

2. It creates tasks:
   "Improve X"
   "Add test for Y"
   "Refactor Z"
   "Find dead code"
   "Fix flaky test"

3. For each task:
   clone repo into disposable sandbox
   run coding agent
   run tests
   run critic
   if accepted: push branch / local patch / PR
   if rejected: iterate N times
   if blocked: ask you

4. Notification policy:
   max 1 question per hour
   max 3 open PRs per repo
   no ping for failed experiments unless novel
   daily digest

## Howto

Core loop: LangGraph

Workers:
  - OpenHands (primary coder)
  - maybe SWE-agent (secondary)

Optional:
  - NemoClaw as experimental “creative agent”

Hard boundaries:
  - each run = new sandbox (VM or runsc)
  - no network
  - readonly repo
  - write only to workspace clone

Control:
  - PR rate limits
  - task budget per hour
  - evaluator must approve

Feedback loop:
  - critic agent
  - test suite
  - static analysis

## What to do

1. NemoClaw/OpenClaw
   easiest to get "something alive" quickly
   worst long-term control

2. OpenHands daemon + cron/queue glue
   moderate effort
   good coding usefulness fast

3. LangGraph supervisor + OpenHands workers
   more effort
   best long-term fit

4. Fully custom agent lab
   maximum effort
   maximum control