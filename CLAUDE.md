# BearPlans — Claude entrypoint

This file remains available for Claude to resume BearPlans. Shared product rules,
architecture, commands, data safety and verification requirements now live in
[AGENTS.md](AGENTS.md). Read that file as part of these instructions; do not maintain
a second copy of its shared rules here.

The single current-work and handoff record is [docs/PROGRESS.md](docs/PROGRESS.md).
Use it to find completed work, active work, recorded checks, pending manual gates,
known guidance discrepancies and the next build. Historical reviews are linked
there; do not pick the newest-looking filename and assume its claims are current.

## Resuming after Codex or a usage limit

1. Read `AGENTS.md`, `docs/PROGRESS.md`, the relevant planning sections and linked
   review evidence before changing files. Shared guidance applies equally when
   Claude resumes code originally written or reviewed by Codex.
2. Inspect Git status, recent commits, the full working diff and relevant untracked
   files. Treat another agent's uncommitted work as unfinished work to understand
   and preserve. Do not restart the project or replace it from an old summary.
3. Compare the tree and test evidence with the current acceptance scenario. State
   what is implemented, incomplete or uncertain; verify previous completion claims
   with appropriate checks rather than treating the summary as proof.
4. Give a brief progress update and immediate next steps, then continue authorized
   work without routine confirmation. The next-build entry is a plan, not a request
   to start application implementation.

## Leaving a useful handoff

Before pausing, reaching a usage limit or transferring work back to Codex, update
`docs/PROGRESS.md` with the exact work state, changed files, commit references,
commands/results, failures/skips, pending manual checks and next concrete action.
Keep incomplete work clearly marked; do not claim completion because usage ran out.
Link the detailed review record and separate implementation and milestone decisions.
Do not rely on Claude's chat/session memory as the only record of a product decision.

Commit only when asked or otherwise explicitly authorized in the current task;
preserve unrelated uncommitted changes. Keep this file substantive and available
for Claude's return. Add future Claude-specific tool/workflow instructions here,
while shared rules and mutable progress remain in their respective documents.
