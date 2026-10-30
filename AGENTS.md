# Working preferences

Conserve the user's usage allowance while completing the requested work correctly.

- Keep scope to the request. Avoid optional refactors, extra deliverables, and speculative improvements.
- Start with targeted `rg` searches; read only relevant file sections. Reuse findings instead of rereading unchanged files.
- Bound tool output. Inspect error summaries and relevant log excerpts; expand when needed to diagnose failures.
- Batch independent reads and searches. Avoid redundant tool calls and polling.
- Use applicable skills only; load references on demand. Avoid adding tools or skills without a concrete need.
- Run required checks and tests appropriate to the change. After they pass, repeat or broaden checks only for new changes, failures, or unresolved risks.
- Use existing scripts for repeated deterministic work. Do not add unnecessary automation.
- Do not spawn subagents unless explicitly requested or required by applicable instructions.
- Keep progress updates and final replies concise. Report the result, meaningful validation, and material limitations without repeating the plan.
- At a natural handoff in a long task, preserve a short state summary rather than a transcript; do not create extra status files for small tasks.
- Do not claim measured savings or changed model/speed settings without evidence.

These preferences do not override higher-priority instructions, required checks, or correctness.
